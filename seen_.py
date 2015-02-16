# coding=utf8
"""
seen.py - A simple Willie module to track nicks
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import json
import os
import re
import threading
from datetime import timedelta, datetime
from time import time

from pytz import timezone

from willie.logger import get_logger
from willie.module import commands, example, priority, rule
from willie.tools import Identifier

LOGGER = get_logger(__name__)

log_regex = re.compile('^#reddit-mlpds_\d{8}\.log$')
line_regex = re.compile('^\[(\d\d:\d\d:\d\d)\] <([^>]+)> (.*)$')
chan_regex = re.compile('^(.*?)_\d{8}$')
cen = timezone("US/Central")  # log timezone
_EXCLUDE = ['#reddit-mlpds-spoilers']

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    # import os.path
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()
try:
    import colors
except:
    import imp
    import sys
    # import os.path
    try:
        LOGGER.info(log.format("Trying manual import of colors."))
        fp, pathname, description = imp.find_module('colors', [os.path.join('.', '.willie', 'modules')])
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
    finally:
        if fp:
            fp.close()


def escape(ucode):
    escaped = ucode
    escaped = re.sub('"', '&quot;', escaped)
    escaped = re.sub("'", '&apos;', escaped)
    return escaped


def unescape(ucode):
    unescaped = ucode
    unescaped = re.sub('&quot;', '"', unescaped)
    unescaped = re.sub('&apos;', "'", unescaped)
    return unescaped


def setup(bot):
    if bot.config.has_option('seen', 'log_dir'):
        bot.memory['seen_log_dir'] = bot.config.seen.log_dir
        LOGGER.info(log.format('found dir %s'), bot.memory['seen_log_dir'])
    else:
        bot.memory['seen_log_dir'] = None

    if 'seen_lock' not in bot.memory:
        bot.memory['seen_lock'] = threading.Lock()

    bot.memory['seen'] = {}

    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    with bot.memory['seen_lock']:
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS seen
                        (nick TEXT NOT NULL, data TEXT, PRIMARY KEY(nick))''')
            dbcon.commit()

            cur.execute('select nick, data from seen')
            dbload = cur.fetchall()
            if dbload:
                for n, d in dbload:
                    data = json.loads(unescape(d))
                    n = Identifier(n)

                    bot.memory['seen'][n.lower()] = (float(data['time']), data['channel'], data['message'])
        finally:
            cur.close()
            dbcon.close()


def seen_insert(bot, nick, data):
    # TODO change data imput to dict

    assert isinstance(nick, str)
    assert isinstance(data, tuple)
    assert len(data) == 3
    assert isinstance(data[0], float), '%r is not float' % data[0]
    assert isinstance(data[1], str)
    assert isinstance(data[2], str)
    nn = Identifier(nick)
    dict = {}
    dict['time'] = str(data[0])
    dict['channel'] = data[1]
    dict['message'] = data[2]

    bot.memory['seen'][nn] = data

    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    try:
        cur.execute('delete from seen where nick = ?', (nn.lower(),))
        cur.execute('''insert into seen (nick, data)
                    values (?, ?)''',
                    (nn.lower(), escape(json.dumps(dict))))
        dbcon.commit()
    finally:
        cur.close()
        dbcon.close()


'''
# TODO
# def seen_delete()
    with bot.memory['seen_lock']:

# TODO
# def seen_ignore()
    with bot.memory['seen_lock']:
'''


@commands('seen_load_logs')
def load_from_logs(bot, trigger):
    """ADMIN: Initializes seen database from log files."""
    if not trigger.owner:
        return
    bot.reply("Alright, I'll start looking through the logs, but this is going to take a while...")
    with bot.memory['seen_lock']:
        LOGGER.info(log.format('=' * 25))
        LOGGER.info(log.format('Starting'))
        filelist = []
        for f in os.listdir(bot.memory['seen_log_dir']):
            if log_regex.match(f) and os.path.isfile(bot.memory['seen_log_dir'] + f):
                filelist.append(bot.memory['seen_log_dir'] + f)
        filelist.sort()
        for log_file in filelist:
            LOGGER.info(log.format('opening %s'), log)
            with open(log_file, 'r') as file:
                file_list = []
                for l in file:
                    # omfg took me way too long to figure out 'replace'
                    file_list.append(l)
                LOGGER.info(log.format('finished loading file'))
                for line in file_list:
                    # line = line
                    # LOGGER.debug(log.format(line))
                    LOGGER.info(log.format('checking line'))
                    m = line_regex.search(line)
                    if m:
                        LOGGER.debug(log.format('line is message'))
                        LOGGER.debug(log.format('%s %s %s'), m.group(1), m.group(2), m.group(3))
                        nn = Identifier(m.group(2))
                        msg = m.group(3)
                        log_name = os.path.splitext(
                            os.path.basename(log_file)
                        )
                        chan = chan_regex.search(log_name[0]).group(1)
                        last = m.group(1)  # 00:00:00
                        date = log_name[0][-8:]  # 20001212
                        dt = datetime(
                            int(date[:4]),
                            int(date[4:6]),
                            int(date[6:]),
                            int(last[:2]),
                            int(last[3:5]),
                            int(last[6:])
                        )
                        utc_dt = cen.normalize(cen.localize(dt))
                        timestamp = float(utc_dt.strftime('%s'))
                        LOGGER.debug(log.format('utc timestamp is %f'), timestamp)
                        data = (timestamp, chan, msg)
                        seen_insert(bot, nn.lower(), data)
    LOGGER.info(log.format('done'))
    bot.reply("Okay, I'm done reading the logs!")


@commands('seen_nuke')
@priority('low')
def seen_nuke(bot, trigger):
    '''ADMIN: Nuke the seen database.'''
    if not trigger.owner:
        LOGGER.warning(log.format(trigger.nick, ' just tried to shush me!'))
        return
    bot.reply("[](/ppsalute) Aye aye, nuking it from orbit.")
    with bot.memory['seen_lock']:
        bot.memory['seen'] = {}  # NUKE IT FROM ORBIT
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            cur.execute('delete from seen')
            dbcon.commit()
        finally:
            cur.close()
            dbcon.close()
        bot.reply("Done!")


@priority('low')
@rule('.*')
def seen_recorder(bot, trigger):
    if trigger.is_privmsg or trigger.sender in _EXCLUDE:
        return  # ignore priv msg and excepted rooms
    nn = Identifier(trigger.nick)
    now = time()
    msg = trigger.args[1].strip()
    chan = trigger.sender

    data = (now, chan, msg)

    with bot.memory['seen_lock']:
        seen_insert(bot, nn.lower(), data)


@commands('seen', 'lastseen')
@example('!seen username')
def seen(bot, trigger):
    '''Reports the last time a nick was seen.'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    LOGGER.info(log.format('triggered custom module'))
    if len(trigger.args[1].split()) == 1:
        bot.reply("Seen who?")
        return
    nn = Identifier(trigger.args[1].split()[1])
    chan = trigger.args[0]

    with bot.memory['seen_lock']:
        if nn == bot.nick:
            bot.reply("[](/ohcomeon \"I'm right here!\")")
        elif nn == trigger.nick:
            bot.reply("What am I, blind?")
        elif nn in bot.memory['seen']:
            last = bot.memory['seen'][nn][0]
            chan = bot.memory['seen'][nn][1]
            msg = bot.memory['seen'][nn][2]

            if msg.startswith("\x01ACTION") and msg.endswith("\x01"):
                msg = "* %s %s" % (nn, msg[7:-1])

            td = timedelta(seconds=(time() - float(last)))
            if td.total_seconds() < (60):
                    t = 'less than a minute ago'
            elif td.total_seconds() < (3600):
                min = td.total_seconds() / 60
                if min != 1:
                    t = '%i minutes ago' % min
                else:
                    t = '1 minute ago'
            elif td.total_seconds() < (60 * 60 * 48):
                hr = td.total_seconds() / 60 / 60
                if hr != 1:
                    t = '%i hours ago' % hr
                else:
                    t = 'about an hour ago' % hr
            else:
                dt = datetime.utcfromtimestamp(last)
                f_datetime = dt.strftime('%b %d, %Y at %H:%M')
                t = 'on %s UTC ' % f_datetime
            bot.reply('I last saw %s in %s %s saying, "%s"' % (
                      colors.colorize(nn, ['purple']),
                      chan,
                      t,
                      colors.colorize(msg, ['green'])
                      ))
            return
        else:
            maybes = []
            for n in bot.memory['seen']:
                res = re.search(trigger.args[1].split()[1], n, flags=re.IGNORECASE)
                if res:
                    maybes.append(n)
            if maybes:
                if len(maybes) <= 20:
                    bot.reply('Perhaps you meant one of the following: %s' % ', '.join(maybes))
                else:
                    bot.reply('Sorry, that returned too many results. Try something more specific.')
            else:
                bot.reply("I've not seen '%s'." % nn)


if __name__ == "__main__":
    print(__doc__.strip())
