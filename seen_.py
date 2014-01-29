"""
seen.py - A simple Willie module to track nicks
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

from time import time
import threading
import os
import re
import json
from pytz import timezone
from types import *
from datetime import timedelta, datetime
import imp
import sys

from willie.tools import Nick
from willie.module import commands, example, priority, rule

log_dir = u''
log_regex = re.compile(u'^#reddit-mlpds_\d{8}\.log$')
line_regex = re.compile(u'^\[(\d\d:\d\d:\d\d)\] <([^>]+)> (.*)$')
chan_regex = re.compile(u'^(.*?)_\d{8}$')
cen = timezone(u"US/Central")  # log timezone
_EXCLUDE = ['#reddit-mlpds-spoilers']


def escape(ucode):
    escaped = ucode
    escaped = re.sub(u'"', u'&quot;', escaped)
    escaped = re.sub(u"'", u'&apos;', escaped)
    return escaped


def unescape(ucode):
    unescaped = ucode
    unescaped = re.sub(u'&quot;', u'"', unescaped)
    unescaped = re.sub(u'&apos;', u"'", unescaped)
    return unescaped

# Bot framework is stupid about importing, so we need to override so that
# the colors module is always available for import.
try:
    import colors
except:
    try:
        fp, pathname, description = imp.find_module('colors',
                                                    ['./.willie/modules/']
                                                    )
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
    finally:
        if fp:
            fp.close()


def setup(bot):
    global log_dir
    if bot.config.has_option('seen', 'log_dir'):
        log_dir = bot.config.seen.log_dir
        bot.debug(u'seen:logdir', u'found dir %s' % log_dir, u'verbose')
    if 'seen_lock' not in bot.memory:
        bot.memory['seen_lock'] = threading.Lock()
    if bot.db and not bot.db.check_table('seen',
                                         ['nick', 'data'],
                                         'nick'
                                         ):
        bot.db.add_table('seen', ['nick', 'data'], 'nick')
    # TODO Initialize preference table for those who wish to not be recorded
    seen_reload(bot)


def seen_reload(bot):
    bot.memory['seen_lock'].acquire()
    try:
        bot.memory['seen'] = {}
        for row in bot.db.seen.keys('nick'):
            nick, json_data = bot.db.seen.get(
                row[0],  # We're getting back ('x',) when we need 'x'
                ('nick', 'data'),
                'nick'
            )
            nn = Nick(nick)
            data = json.loads(unescape(json_data))
            tm = float(data['time'])
            assert type(tm) is FloatType, u'%r is not float' % tm
            chan = data['channel']
            msg = data['message']
            r_tup = (tm, chan, msg)
            bot.memory['seen'][nn.lower()] = r_tup
    finally:
        bot.memory['seen_lock'].release()


def seen_insert(bot, nick, data):
    # TODO change data imput to dict
    # TODO Just pass data through to databasae

    assert isinstance(nick, basestring)
    assert type(data) is TupleType
    assert len(data) == 3
    assert type(data[0]) is FloatType, u'%r is not float' % data[0]
    assert isinstance(data[1], basestring)
    assert isinstance(data[2], basestring)
    nn = Nick(nick)
    dict = {}
    dict['time'] = str(data[0])
    dict['channel'] = data[1]  # data[1] should be unicode
    dict['message'] = data[2]

    bot.memory['seen'][nn] = data
    #bot.debug('to insert', '%s, %r' % (nn.lower(), dict) ,'verbose')
    bot.db.seen.update(nn.lower(), {'data': escape(json.dumps(dict))})


'''
# TODO
#def seen_delete()
    bot.memory['seen_lock'].acquire()
    try:
    finally:
        bot.memory['seen_lock'].release()

# TODO
#def seen_ignore()
    bot.memory['seen_lock'].acquire()
    try:
    finally:
        bot.memory['seen_lock'].release()
'''


@commands(u'seen_load_logs')
def load_from_logs(bot, trigger):
    if trigger.owner:
        bot.reply(u"Alright, I'll start looking through the logs, " +
                  u"but this is going to take a while..."
                  )
        bot.memory['seen_lock'].acquire()
        try:
            bot.debug(u'load_from_logs', u'=' * 25, u'verbose')
            bot.debug(u'load_from_logs', u'Starting', u'verbose')
            filelist = []
            for f in os.listdir(log_dir):
                if log_regex.match(f) and os.path.isfile(log_dir + f):
                    filelist.append(log_dir + f)
            filelist.sort()
            for log in filelist:
                bot.debug(u'%f load_from_logs' % time(),
                          u'opening %s' % log,
                          u'verbose'
                          )
                with open(log, 'r') as file:
                    file_list = []
                    for l in file:
                        # omfg took me way too long to figure out 'replace'
                        file_list.append(l.decode('utf-8', 'replace'))
                    bot.debug(u'%f' % time(),
                              u'finished loading file',
                              u'verbose'
                              )
                    for line in file_list:
                        #line = line.decode('utf-8', 'replace')
                        #bot.debug('load_from_logs: line', line,'verbose')
                        bot.debug(u'%f' % time(),
                                  u'checking line',
                                  u'verbose'
                                  )
                        m = line_regex.search(line)
                        if m:
                            '''bot.debug(
                                    'load_from_logs',
                                    'line is message',
                                    'verbose'
                                    )'''
                            '''bot.debug(
                                    'line',
                                    '%s %s %s' % (
                                        m.group(1),
                                        m.group(2),
                                        m.group(3)
                                        ),
                                    'verbose'
                                    )'''
                            nn = Nick(m.group(2))
                            msg = m.group(3)
                            log_name = os.path.splitext(
                                os.path.basename(log)
                            )
                            chan = chan_regex.search(log_name[0]).group(1)
                            chan = chan.decode('utf-8', 'replace')
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
                            timestamp = float(utc_dt.strftime(u'%s'))
                            '''bot.debug(
                                    'logname',
                                    'utc timestamp is %f' % timestamp,
                                    'verbose'
                                    )'''
                            data = (timestamp, chan, msg)
                            seen_insert(bot, nn.lower(), data)
        finally:
            bot.memory['seen_lock'].release()
        bot.debug(u'', u'done', u'verbose')
        bot.reply(u"Okay, I'm done reading the logs!")


@commands('nuke')
@priority('low')
def seen_nuke(bot, trigger):
    '''ADMIN: Nuke the seen database'''
    if trigger.owner:
        bot.reply(u"[](/ppsalute) Aye aye, nuking it from orbit.")
        bot.memory['seen_lock'].acquire()
        try:
            bot.memory['seen'] = {}  # NUKE IT FROM ORBIT
            for row in bot.db.seen.keys('nick'):
                bot.db.seen.delete(row[0], 'nick')
            bot.reply(u"Done!")
        finally:
            bot.memory['seen_lock'].release()
    else:
        bot.debug(
            u'seen.py:nuke',
            u'%s just tried to use the !nuke command!' % trigger.nick,
            u'always'
        )


@priority(u'low')
@rule(u'.*')
def seen_recorder(bot, trigger):
    if not trigger.args[0].startswith(u'#') or trigger.sender in _EXCLUDE:
        return  # ignore priv msg and excepted rooms
    nn = Nick(trigger.nick)
    now = time()
    msg = trigger.args[1].strip().encode('utf-8', 'replace')
    chan = trigger.args[0].encode('utf-8', 'replace')

    data = (now, chan, msg)

    bot.memory['seen_lock'].acquire()
    try:
        seen_insert(bot, nn.lower(), data)
    finally:
        bot.memory['seen_lock'].release()


@commands('seen')
@example(u'!seen tdreyer1')
def seen(bot, trigger):
    '''Reports the last time a nick was seen.'''
    bot.debug(u'seen:seen', u'triggered custom module', u'verbose')
    if len(trigger.args[1].split()) == 1:
        bot.reply(u"Seen who?")
        return
    nn = Nick(trigger.args[1].split()[1])
    chan = trigger.args[0]

    with bot.memory['seen_lock']:
        if nn == bot.nick:
            bot.reply(u"[](/ohcomeon \"I'm right here!\")")
        elif nn == trigger.nick:
            bot.reply(u"What am I, blind?")
        elif nn in bot.memory['seen']:
            last = bot.memory['seen'][nn][0]
            chan = bot.memory['seen'][nn][1]
            msg = bot.memory['seen'][nn][2]

            if msg.startswith("\x01ACTION") and msg.endswith("\x01"):
                msg = "* %s %s" % (nn, msg[7:-1])

            td = timedelta(seconds=(time() - float(last)))
            if td.total_seconds() < (60):
                    t = u'less than a minute ago'
            elif td.total_seconds() < (3600):
                min = td.total_seconds() / 60
                if min != 1:
                    t = u'%i minutes ago' % min
                else:
                    t = u'1 minute ago'
            elif td.total_seconds() < (60 * 60 * 48):
                hr = td.total_seconds() / 60 / 60
                if hr != 1:
                    t = u'%i hours ago' % hr
                else:
                    t = u'about an hour ago' % hr
            else:
                dt = datetime.utcfromtimestamp(last)
                f_datetime = dt.strftime('%b %d, %Y at %H:%M')
                t = u'on %s UTC ' % f_datetime
            bot.reply(u'I last saw %s in %s %s saying, "%s"' % (
                      colors.colorize(nn, [u'purple']),
                      chan,
                      t,
                      colors.colorize(msg, [u'blue'])
                      ))
            return
        else:
            maybes = []
            for n in bot.memory['seen']:
                res = re.search(trigger.args[1].split()[1], n, flags=re.IGNORECASE)
                if res:
                    maybes.append(n)
            if maybes:
                if len(maybes) <= 10:
                    bot.reply(u'Perhaps you meant one of the following: %s' % u', '.join(maybes))
                else:
                    bot.reply(u'Sorry, that returned too many results. Try something more specific.')
            else:
                bot.reply(u"I've not seen '%s'." % nn)


if __name__ == "__main__":
    print __doc__.strip()
