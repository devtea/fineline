"""
episodes.py - A simple willie module to return and modify TV episodes
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import random
import re
import threading
from willie.module import commands, example

random.seed()

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


def setup(bot):
    if 'ep_lock' not in bot.memory:
        bot.memory['ep_lock'] = threading.Lock()
    with bot.memory['ep_lock']:
        bot.memory['episodes'] = {}
        dbeps = None
        dbcon = bot.db.connect()  # sqlite3 connection
        cur = dbcon.cursor()
        try:
            # if our tables don't exist, create them
            cur.execute('''CREATE TABLE IF NOT EXISTS episodes
                           (season int, episode int, title text)''')
            dbcon.commit()

            cur.execute('SELECT season, episode, title FROM episodes')
            dbeps = cur.fetchall()
        finally:
            cur.close()
            dbcon.close()
        if dbeps:
            for s, e, t in dbeps:
                if s not in bot.memory['episodes']:
                    bot.memory['episodes'][s] = {}
                bot.memory['episodes'][s][e] = t


def get_ep(bot, se):
    """Accepts a list containing season and episode"""
    if len(se) == 2 and se[0] in bot.memory['episodes'] and se[1] in bot.memory['episodes'][se[0]]:
            title = bot.memory['episodes'][se[0]][se[1]]
            return u"The episode is season %i, episode %i, %s." % (
                se[0], se[1], title)
    return u"I can't seem to find that episode."


@commands(u'ep-del')
def ep_del(bot, trigger):
    """ADMIN: Deletes a specified episode from the database."""
    # test the arguments returned, e.g. ['.episode', 'S01E03']
    if len(trigger.args[1].split()) == 2:
        # Test the second argument for sanity, eg 'S01E03'
        if re.match(ur'^S\d{1,2}E\d{1,2}$',
                    trigger.args[1].split()[1],
                    flags=re.IGNORECASE
                    ):
            season, __, ep = trigger.args[1].split()[1].upper().partition(u"E")
            season = int(season[1:])
            ep = int(ep)
            with bot.memory['ep_lock']:
                dbcon = bot.db.connect()  # sqlite3 connection
                cur = dbcon.cursor()
                try:
                    cur.execute('''SELECT count(*) FROM episodes
                                WHERE season = ? and episode = ?''', (season, ep))
                    count = int(cur.fetchall()[0][0])
                    if count != 0:
                        cur.execute('''DELETE from episodes
                                    WHERE season = ? and episode = ?''', (season, ep))
                        dbcon.commit()
                    else:
                        bot.reply(u'That episode doesn\'t exist!')
                        return
                    del bot.memory['episodes'][season][ep]
                    if len(bot.memory['episode'][season]) == 0:
                        del bot.memory['episode'][season]
                    bot.reply(u'Episode deleted.')
                finally:
                    cur.close()
        else:
            bot.reply(u"I don't understand that. Try something like !ep-del s02e01")
    elif len(trigger.args[1].split()) > 2:
        bot.reply(u"I don't understand that, too many args.")
    else:
        bot.reply(u"Try something like !ep-del s02e01")


@commands(u'ep-add')
@example(u'!ep-add S00E00 This is not a title')
def add_ep(bot, trigger):
    """ADMIN: Adds an episode to the database."""
    bot.debug(__file__, log.format(u"add_ep triggered"), u"verbose")
    if not trigger.admin:
        bot.debug(__file__, log.format(trigger.nick, u" just tried to add an episode..."), u"always")
        return
        # assume input is SxxExx title~~~~~~
        # eg ['!test', 'S01E01', 'Title', ...]
    command = trigger.args[1].split()
    if len(command) > 2:
        # Test the second argument for sanity, eg 'S01E03'
        if re.match(ur'^S\d{1,2}E\d{1,2}$',
                    command[1],
                    flags=re.IGNORECASE
                    ):
            bot.debug(__file__, log.format(u"Ep is sane"), u"verbose")
            season, __, ep = trigger.args[1].split()[1].upper().partition("E")
            season = int(season.lstrip("S"))
            ep = int(ep)
            title = u' '.join(i for i in command if command.index(i) > 1)
            bot.debug(__file__, log.format(u'Season %i, episode %i' % (season, ep)), u'verbose')
            message = get_ep(bot, [season, ep])
            if message.startswith(u'T'):
                bot.reply(u"That episode already exists!")
                bot.reply(message)
            else:
                with bot.memory['ep_lock']:
                    dbcon = bot.db.connect()  # sqlite3 connection
                    cur = dbcon.cursor()
                    try:
                        cur.execute('''select count(*) from episodes
                                where season = ? and episode = ?''', (season, ep))
                        count = int(cur.fetchall()[0][0])
                        if count == 0:
                            cur.execute('''insert into episodes (season, episode, title )
                                        values (?, ?, ?)''', (season, ep, title))
                            dbcon.commit()
                        else:
                            bot.reply(u'That episode already exists')
                        if season not in bot.memory['episodes']:
                            bot.memory['episodes'][season] = {}
                        bot.memory['episodes'][season][ep] = title
                        bot.reply(u"Successfully added!")
                    finally:
                        cur.close()
        else:
            bot.debug(__file__, log.format(u"Argument is insane"), u"verbose")
            bot.reply(u"I don't understand that.")
    else:
        bot.debug(__file__, log.format(u"Not enough args"), u"verbose")
        bot.reply(u"Uh, what episode?")


@commands(u'episode', u'ep')
@example(u'!episode S02E11')
def episode(bot, trigger):
    """Returns a specified episode by season and episode."""
    bot.debug(__file__, log.format(u"Triggered"), u"verbose")
    # test the arguments returned, e.g. ['.episode', 'S01E03']
    if len(trigger.args[1].split()) == 2:
        # Test the second argument for sanity, eg 'S01E03'
        if re.match(ur'^S\d{1,2}E\d{1,2}$',
                    trigger.args[1].split()[1],
                    flags=re.IGNORECASE
                    ):
            bot.debug(__file__, log.format(u"Argument is sane"), u"verbose")
            season, __, ep = trigger.args[1].split()[1].upper().partition(u"E")
            bot.reply(get_ep(bot, [int(season.lstrip(u"S")), int(ep)]))
        else:
            bot.debug(__file__, log.format(u"Argument is insane"), u"verbose")
            bot.reply((u"I don't understand that. Try '%s: help " +
                       u"episode'") % bot.nick)
    elif len(trigger.args[1].split()) > 2:
        bot.debug(__file__, log.format(u"too many args"), u"verbose")
        bot.reply(u"I don't understand that. Try '%s: help episode'" % bot.nick)
    else:
        bot.debug(__file__, log.format(u"Not enough args"), u"verbose")
        randep(bot, trigger)


@commands(u'randep', u'rep', u'randomep')
def randep(bot, trigger):
    """Returns a random episode."""
    bot.debug(__file__, log.format(u"Triggered"), u"verbose")
    season = random.randint(1, len(bot.memory['episodes']))
    episode = random.randint(1, len(bot.memory['episodes'][season]))
    bot.reply(get_ep(bot, [season, episode]))


if __name__ == "__main__":
    print(__doc__.strip())
