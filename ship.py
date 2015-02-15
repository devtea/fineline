"""
ship.py - A Willie module that 'ships' to characters from database list
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import bisect
import os.path
import random
import threading
from datetime import datetime
from types import IntType

from willie.logger import get_logger
from willie.module import commands, example
from willie.tools import Identifier

LOGGER = get_logger(__name__)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()

try:
    import nicks
except:
    import imp
    import sys
    try:
        LOGGER.info(log.format("trying manual import of nicks"))
        fp, pathname, description = imp.find_module('nicks', [os.path.join('.', '.willie', 'modules')])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()

_front = ['any', 'some']
_back = ['one', 'body', 'pony', 'poni', 'pone']
_anyone = [a + b for a in _front for b in _back]
_reply_list = [u'%s x %s',
               u'%s and %s didn\'t choose the huglife, the huglife chose them.',
               u'%s and %s can\'t keep their hooves off each other',
               u'%s and %s are suddenly and inexplicably attracted to each other...',
               u'%s gets unceremoniously stuffed into a shipping container with %s.',
               u'%s and %s set sail.',
               u'%s and %s sail the seven seas.',
               u'%s and %s are caught redhoofed.',
               u'%s and %s will deny it, but everypony knows...',
               u'%s writes a self-insert fanfic about %s.',
               u'%s and %s take the midnight train going anywhere.',
               u'%s and %s "accidentally" find themselves together in a hotel room... Alone...',
               u'That\'s right, %s and %s...',
               u'%s and %s find some creative ways to entertain themselves.',
               u'%s and %s forgot to leave room for Jesus!',
               u'%s and %s have a party of two.',
               u'%s and %s have more in common than they thought!',
               u'%s sets aside some "special hugging" time for %s',
               u'%s brings the duct tape, %s brings the WD40...',
               u'%s could not get any closer to %s right now.',
               u'%s stares at %s, lost forever in their dreamy eyes.',
               u'%s blushes as %s leans in for a peck.',
               u'%s nearly faints when %s senpai finally notices them~',
               u'%s isn\'t the only one chasing after %s',
               u'%s only has eyes for %s',
               u'It\'s hard to tell where %s ends and %s begins.',
               u'%s has a super secret diary just filled with pictures of %s.'
               ]


def setup(bot):
    if 'pony_list_lock' not in bot.memory:
        bot.memory['pony_list_lock'] = threading.Lock()
    with bot.memory['pony_list_lock']:
        if 'pony_list' not in bot.memory or not bot.memory['pony_list']:
            bot.memory['pony_list'] = []

            dbcon = bot.db.connect()
            cur = dbcon.cursor()

            try:
                cur.execute('select name, weight from prompt_ponies')
                pony_rows = cur.fetchall()
            finally:
                cur.close()
                dbcon.close()
            if pony_rows:
                for name, weight in pony_rows:
                    bot.memory['pony_list'].append((name, weight))


def weighted_choice(weighted):
    """Returns a random index from a list of tuples that contain
    (something, weight) where weight is the weighted probablity that
    that item should be chosen. Higher weights are chosen more often"""

    sum = 0
    sum_steps = []
    for item in weighted:
        sum = sum + int(item[1])
        sum_steps.append(sum)
    return bisect.bisect_right(sum_steps, random.uniform(0, sum))


@commands(u'ship')
def ship(bot, trigger):
    """Returns a somewhat random shipping pair."""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    include_nicks = False
    try:
        target = nicks.NickPlus(trigger.args[1].split()[1])
    except IndexError:
        target = None
    else:
        if target.lower() in ['me', 'myself']:
            target = trigger.nick
            include_nicks = True
        elif target.lower() in ['yourself', 'you']:
            target = bot.nick
            include_nicks = True
        elif target.lower() in _anyone:
            # select a random nick from the channel
            # don't match lurkers

            # seen_.py:203/128:
            #     data = (timestamp, chan, msg)
            #     bot.memory['seen'][nn] = data
            #     where nn is Identifier(nick)
            #     timestamp is a float
            target = None
            target_list = nicks.in_chan(bot, trigger.sender)
            random.shuffle(target_list)
            now = datetime.now()
            for nick in target_list:
                timedelta = now - last_seen(bot, nick)
                if timedelta.days <= 3:  # magic numbers are magic
                    target = nick
                    include_nicks = True
                    break

        elif nicks.in_chan(bot, trigger.sender, target):
            # Get properly formatted nick from channel nick list
            nick_list = []
            nick_list.extend(nicks.in_chan(bot, trigger.sender))
            i = nicks.in_chan(bot, trigger.sender).index(target)
            target = nick_list.pop(i)

            LOGGER.info(log.format("target is: %s"), target)
            include_nicks = True
        else:
            LOGGER.info(log.format('Target not found in room.'))
            target = None

    if target or include_nicks:
        i1 = target
    else:
        i1 = weighted_choice(bot.memory['pony_list'])
    i2 = i1
    if include_nicks and random.uniform(0, 1) > 0.5:
        # match target with nick in channel
        # don't match lurkers
        target_list = nicks.in_chan(bot, trigger.sender)
        random.shuffle(target_list)
        now = datetime.now()
        for nick in target_list:
            timedelta = now - last_seen(bot, nick)
            if nick != i1 and timedelta.days <= 3:  # magic numbers are magic
                i2 = nick
                break

        pair = [i1, i2]
    else:
        # match nick with pony!
        while unicode(i2) == unicode(i1):
            i2 = weighted_choice(bot.memory['pony_list'])
        if not isinstance(i1, IntType):
            pair = [i1, bot.memory['pony_list'][i2][0]]
        else:
            pair = [bot.memory['pony_list'][i1][0], bot.memory['pony_list'][i2][0]]
    random.shuffle(pair)
    bot.reply(random.choice(_reply_list) % (pair[0], pair[1]))


@commands(u'ship_delname')
@example(u'!ship_delname some name')
def delname(bot, trigger):
    '''ADMIN: Removes a pony from the database. Admin only.'''
    if not trigger.admin:
        return
    name = ' '.join(trigger.split(u' ')[1:]).lower()
    LOGGER.info(log.format(name))
    with bot.memory['pony_list_lock']:
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            cur.execute('select name, weight from prompt_ponies where lower(name) = ?', (name,))
            rows = cur.fetchall()
            LOGGER.info(log.format(u'%s'), rows)
            if rows:
                cur.execute('delete from prompt_ponies where lower(name) = ?', (name,))
                dbcon.commit()
                bot.memory['pony_list'] = [x for x in bot.memory['pony_list'] if x[0].lower() != name]
                bot.reply(u'Deleted %s (%s) from the list.' % (rows[0][0], rows[0][1]))
            else:
                bot.reply(u'%s was not found in the list.' % name)
        finally:
            cur.close()
            dbcon.close()


@commands(u'ship_addname')
@example(u'!ship_addname some name 1000')
def addname(bot, trigger):
    '''Adds a character name and weight to the database. Admin only.'''
    if not trigger.admin:
        return
    command = trigger.args[1].split(' ')
    if len(command) < 3:
        bot.reply('Not enough arguments. Needs name and weight.')
        return
    try:
        weight = int(command.pop(-1))
    except:
        bot.reply('Invalid weight. Final argument must be an integer.')
        return
    command.pop(0)
    name = ' '.join(command)
    LOGGER.info(log.format('name: "%s", weight: "%i"'), name, weight)
    with bot.memory['pony_list_lock']:
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            cur.execute('''insert into prompt_ponies (name, weight)
                           values (?, ?)''', (name, weight))
            dbcon.commit()
            bot.memory['pony_list'].append((name, weight))
            bot.reply(u'Done')
        finally:
            cur.close()
            dbcon.close()


def last_seen(bot, nick):
    '''returns the last time the nick was seen as a datetime object'''
    nn = Identifier(nick)
    try:
        tm, channel, message = bot.memory['seen'][nn]
        return datetime.fromtimestamp(float(tm))
    except:
        return datetime.fromtimestamp(0)


if __name__ == "__main__":
    print(__doc__.strip())
