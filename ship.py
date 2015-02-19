"""
ship.py - A Willie module that 'ships' to characters from database list
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import bisect
import random
import threading
from datetime import datetime

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
    import os.path
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
    import os.path
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
_reply_list = ['%s x %s',
               '%s and %s didn\'t choose the huglife, the huglife chose them.',
               '%s and %s can\'t keep their hooves off each other',
               '%s and %s are suddenly and inexplicably attracted to each other...',
               '%s gets unceremoniously stuffed into a shipping container with %s.',
               '%s and %s set sail.',
               '%s and %s sail the seven seas.',
               '%s and %s are caught redhoofed.',
               '%s and %s will deny it, but everypony knows...',
               '%s writes a self-insert fanfic about %s.',
               '%s and %s take the midnight train going anywhere.',
               '%s and %s "accidentally" find themselves together in a hotel room... Alone...',
               'That\'s right, %s and %s...',
               '%s and %s find some creative ways to entertain themselves.',
               '%s and %s forgot to leave room for Jesus!',
               '%s and %s have a party of two.',
               '%s and %s have more in common than they thought!',
               '%s sets aside some "special hugging" time for %s',
               '%s brings the duct tape, %s brings the WD40...',
               '%s could not get any closer to %s right now.',
               '%s stares at %s, lost forever in their dreamy eyes.',
               '%s blushes as %s leans in for a peck.',
               '%s nearly faints when %s senpai finally notices them~',
               '%s isn\'t the only one chasing after %s',
               '%s only has eyes for %s',
               'It\'s hard to tell where %s ends and %s begins.',
               '%s has a super secret diary just filled with pictures of %s.'
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


@commands('ship')
def ship(bot, trigger):
    """Returns a somewhat random shipping pair."""
    LOGGER.debug(log.format('Ship module started'))
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        LOGGER.debug(log.format('Ship returning, shushed'))
        return
    include_nicks = False
    try:
        target = nicks.NickPlus(trigger.args[1].split()[1])
        LOGGER.debug(log.format('Found target=%s'), target)
    except IndexError:
        target = None
        LOGGER.debug(log.format('No target specified'))
    else:
        if target.lower() in ['me', 'myself']:
            LOGGER.debug(log.format('"ship me" format'))
            target = trigger.nick
            include_nicks = True
        elif target.lower() in ['yourself', 'you']:
            LOGGER.debug(log.format('"ship you" format'))
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
            LOGGER.debug(log.format('"ship anyone" format'))
            target = None
            target_list = nicks.in_chan(bot, trigger.sender)
            random.shuffle(target_list)
            now = datetime.now()
            for nick in target_list:
                timedelta = now - last_seen(bot, nick)
                if timedelta.days <= 3:  # magic numbers are magic
                    target = nick
                    LOGGER.debug(log.format('Nick selected: %s'), nick)
                    include_nicks = True
                    break
        elif nicks.in_chan(bot, trigger.sender, target):
            LOGGER.debug(log.format('"ship nickname" format'))
            # Get properly formatted nick from channel nick list
            nick_list = []
            nick_list.extend(nicks.in_chan(bot, trigger.sender))
            LOGGER.debug(log.format('nick_list: %s'), nick_list)
            i = nicks.in_chan(bot, trigger.sender).index(target)
            target = nick_list.pop(i)
            LOGGER.debug(log.format('target: %s index: %s'), target, i)
            include_nicks = True
        else:
            LOGGER.debug(log.format('Target not found in room.'))
            target = None

    if target or include_nicks:
        LOGGER.debug(log.format("Target was specified at some point so we'll include nicks in chan."))
        i1 = target
        LOGGER.debug(log.format('i1=%s'), i1)
    else:
        LOGGER.debug(log.format("Target was not specified at some point so we'll only pull from database list."))
        i1 = weighted_choice(bot.memory['pony_list'])  # This gets the index, not the key
        LOGGER.debug(log.format('i1=%s'), i1)
    LOGGER.debug(log.format('Setting i2 = i1'))
    i2 = i1
    if include_nicks and random.uniform(0, 1) > 0.5:
        # This will never run with i1,i2 being indexes due to include_nicks

        # match target with nick in channel
        # don't match lurkers
        target_list = nicks.in_chan(bot, trigger.sender)
        random.shuffle(target_list)
        now = datetime.now()
        for nick in target_list:
            timedelta = now - last_seen(bot, nick)
            LOGGER.debug(log.format('comparing nick=%s i1=%s timedelta=%s'), nick, i1, timedelta.days)
            if nick != i1 and timedelta.days <= 3:  # magic numbers are magic
                i2 = nick
                break
        if i1 == i2:  # Edge case, no nicks matched criteria so i1 still == i2
            LOGGER.debug(log.format('Edge case! i1 still equals i2'))
            target_list = nicks.in_chan(bot, trigger.sender)
            random.shuffle(target_list)
            for nick in target_list:
                LOGGER.debug(log.format('recomparing nick=%s (%s) i1=%s (%s)'), nick, type(nick), i1, type(i1))
                if nick != i1:
                    LOGGER.debug(log.format('nick != i1'))
                    i2 = nick
                    break
                else:
                    LOGGER.debug(log.format('nick == i1'))
        pair = [i1, i2]
        LOGGER.debug(log.format('i1=%s, i2=%s'), i1, i2)
    else:
        # This can run with i1,i2 being either indexes or nicks!
        if isinstance(i1, int):
            i1 = bot.memory['pony_list'][i1][0]
            i2 = i1
        # match nick with pony!
        LOGGER.debug(log.format('i1=%s, i2=%s'), i1, i2)
        while i2 == i1:
            i2 = weighted_choice(bot.memory['pony_list'])
            i2 = bot.memory['pony_list'][i2][0]
            LOGGER.debug(log.format('i1=%s, i2=%s'), i1, i2)
        pair = [i1, i2]
        '''
        if not isinstance(i1, int):
            pair = [i1, bot.memory['pony_list'][i2][0]]
        else:
            pair = [bot.memory['pony_list'][i1][0], bot.memory['pony_list'][i2][0]]
        '''
    random.shuffle(pair)
    bot.reply(random.choice(_reply_list) % (pair[0], pair[1]))


@commands('ship_delname')
@example('!ship_delname some name')
def delname(bot, trigger):
    '''ADMIN: Removes a pony from the database. Admin only.'''
    if not trigger.admin:
        return
    name = ' '.join(trigger.split(' ')[1:]).lower()
    LOGGER.info(log.format(name))
    with bot.memory['pony_list_lock']:
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            cur.execute('select name, weight from prompt_ponies where lower(name) = ?', (name,))
            rows = cur.fetchall()
            LOGGER.info(log.format('%s'), rows)
            if rows:
                cur.execute('delete from prompt_ponies where lower(name) = ?', (name,))
                dbcon.commit()
                bot.memory['pony_list'] = [x for x in bot.memory['pony_list'] if x[0].lower() != name]
                bot.reply('Deleted %s (%s) from the list.' % (rows[0][0], rows[0][1]))
            else:
                bot.reply('%s was not found in the list.' % name)
        finally:
            cur.close()
            dbcon.close()


@commands('ship_addname')
@example('!ship_addname some name 1000')
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
            bot.reply('Done')
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
