"""
karma.py - A willie module to keep track of "points" for arbitrary things
Copyright 2013, Khyperia, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import threading
import time

from willie.module import commands, example, rule, priority
from willie.tools import Nick

_ignore = ['hushmachine']


def setup(bot):
    if 'karma_lock' not in bot.memory:
        bot.memory['karma_lock'] = threading.Lock()
    if 'karma_time' not in bot.memory:
        bot.memory['karma_time'] = {}
    bot.memory['karma'] = {}

    with bot.memory['karma_lock']:
        dbcon = bot.db.connect()  # sqlite3 connection
        cur = dbcon.cursor()
        try:
            #if our tables don't exist, create them
            cur.execute('''CREATE TABLE IF NOT EXISTS karma
                           (tag text, score int)''')
            dbcon.commit()

            cur.execute('SELECT tag, score from karma')
            dbload = cur.fetchall()
        finally:
            cur.close()
            dbcon.close()
        if dbload:
            for t, s in dbload:
                bot.memory['karma'][t] = s


@priority(u'low')
@rule(u'[^!]*(\+\+|--)$')
def karmaRule(bot, trigger):
    if trigger.sender[0] != '#':
        return
    if trigger.nick in _ignore:
        return
    obj = trigger.bytes.strip()
    if not obj or len(obj) < 3:
        return
    shortobj = obj[:-2].lower().strip()

    #don't let users karma themselves
    if shortobj.lower() == trigger.nick.lower().strip('_`'):
        return

    with bot.memory['karma_lock']:
        newkarm = None
        if timecheck(bot, trigger):
            if obj.endswith("++"):
                newkarm = modkarma(bot, shortobj, 1)
            elif obj.endswith("--"):
                newkarm = modkarma(bot, shortobj, -1)
            bot.reply("Karma for %s is at %i" % (shortobj, newkarm))
        else:
            bot.reply(u"You just used karma! You can't use it again for a bit.")


def timecheck(bot, trigger):
    if trigger.admin:
        return True
    if Nick(trigger.nick) in bot.memory['karma_time'] \
            and time.time() < bot.memory['karma_time'][Nick(trigger.nick)] + 60:
        return False
    bot.memory['karma_time'][Nick(trigger.nick)] = time.time()
    return True


@commands('karma')
@example(u'!karma fzoo')
def karma(bot, trigger):
    obj = trigger.bytes[7:].lower().strip()
    if not obj:
        return
    karm = modkarma(bot, obj, 0)
    bot.reply("Karma for %s is at %i" % (obj, karm))


def modkarma(bot, obj, amount):
    dbcon = bot.db.connect()  # sqlite3 connection
    cur = dbcon.cursor()

    try:
        if obj in bot.memory['karma']:
            bot.memory['karma'][obj] += amount
            cur.execute('''UPDATE karma set score = ?
                        where tag = ?''',
                        (bot.memory['karma'][obj], obj))
        else:
            bot.memory['karma'][obj] = amount
            cur.execute('''INSERT into karma (tag, score)
                            VALUES (?, ?)''',
                        (obj, bot.memory['karma'][obj]))
        dbcon.commit()
        return bot.memory['karma'][obj]
    finally:
        cur.close()
        dbcon.close()


if __name__ == "__main__":
    print __doc__.strip()
