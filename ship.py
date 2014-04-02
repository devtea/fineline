"""
ship.py - A Willie module that 'ships' to characters from database list
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import bisect
import random
import threading

from willie.module import commands

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        print("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', ['./.willie/modules/'])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()

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
               u'%s and %s "accidentally" find themselves together in a hotel room... Alone...'
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
    i1 = weighted_choice(bot.memory['pony_list'])
    i2 = i1
    while i2 == i1:
        i2 = weighted_choice(bot.memory['pony_list'])
    pair = (bot.memory['pony_list'][i1][0],
            bot.memory['pony_list'][i2][0]
            )
    bot.reply(random.choice(_reply_list) % pair)


@commands(u'ship_delname')
def delname(bot, trigger):
    '''ADMIN: Removes a pony from the database. Admin only.'''
    if not trigger.admin:
        return
    name = ' '.join(trigger.split(u' ')[1:]).lower()
    bot.debug(__file__, log.format(name), 'verbose')
    with bot.memory['pony_list_lock']:
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            cur.execute('select name, weight from prompt_ponies where lower(name) = ?', (name,))
            rows = cur.fetchall()
            bot.debug(__file__, log.format(u'%s' % rows), u'verbose')
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
def addname(bot, trigger):
    '''ADMIN: Adds a pony to the database. Admin only.'''
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
    bot.debug(__file__, log.format('name: "%s", weight: "%i"' % (name, weight)), 'verbose')
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


if __name__ == "__main__":
    print(__doc__.strip())
