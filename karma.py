"""
karma.py - A willie module to keep track of "points" for arbitrary things
Copyright 2013, Khyperia, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import threading
import time

from willie.module import commands, example, rule, priority


def setup(bot):
    if 'karma_lock' not in bot.memory:
        bot.memory['karma_lock'] = threading.Lock()
    if 'karma_time' not in bot.memory:
        bot.memory['karma_time'] = {}
    if 'karma' in bot.memory:
        for i in bot.memory['karma']:
            print '%s: %i' % (i, bot.memory['karma'][i])
    print 'klearing karma'
    bot.memory['karma'] = {}
    if 'karma' in bot.memory:
        for i in bot.memory['karma']:
            print '%s: %i' % (i, bot.memory['karma'][i])

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
@rule(u'.*')
def karmaRule(bot, trigger):
    if trigger.sender[0] != '#':
        return
    obj = trigger.bytes.strip()
    if not obj or len(obj) < 3:
        return
    shortobj = obj[:-2].lower().strip()

    with bot.memory['karma_lock']:
        newkarm = None
        if obj.endswith("++") and timecheck(bot, trigger):
            newkarm = modkarma(bot, shortobj, 1)
        elif obj.endswith("--") and timecheck(bot, trigger):
            newkarm = modkarma(bot, shortobj, -1)

    if newkarm:
        bot.reply("Karma for %s is at %i" % (shortobj, newkarm))


def timecheck(bot, trigger):
    if trigger.admin:
        return True
    if trigger.sender in bot.memory['karma_time'] and time.time() < bot.memory['karma_time'][trigger.sender] + 60:
        bot.reply(u"You just used karma! You can't use it again for a bit.")
        return False
    bot.memory['karma_time'][trigger.sender] = time.time()
    return True


@commands('karma')
@example(u'!karma fzoo')
def karma(bot, trigger):
    obj = trigger.bytes[7:].lower().strip()
    karm = modkarma(bot, obj, 0)
    if karm:
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
