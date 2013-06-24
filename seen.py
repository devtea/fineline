"""
seen.py - A simple willie module to track nicks
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from time import time
import threading
import os
import re
import pytz
import json
from pytz import timezone
from types import *
from datetime import timedelta, datetime

from willie.tools import Nick

import colors


log_dir = u''
log_regex = re.compile('^#reddit-mlpds_\d{8}\.log$')
line_regex = re.compile('^\[(\d\d:\d\d:\d\d)\] <([^>]+)> (.*)$')
chan_regex = re.compile('^(.*?)_\d{8}$')
cen = timezone("US/Central")  #log timezone


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


def setup(willie):
    global log_dir
    if willie.config.has_option('seen', 'log_dir'):
        log_dir = willie.config.seen.log_dir
        willie.debug('seen:logdir', 'found dir %s' % log_dir, 'verbose')
    if 'seen_lock' not in willie.memory:
        willie.memory['seen_lock'] = threading.Lock()
    if willie.db and not willie.db.check_table(
            'seen',
            ['nick', 'data'],
            'nick'
            ):
        willie.db.add_table('seen', ['nick', 'data'], 'nick')
    # TODO Initialize preference table for those who wish to not be recorded
    seen_reload(willie)


def seen_reload(willie):
    willie.memory['seen_lock'].acquire()
    try:
        willie.memory['seen'] = {}
        for row in willie.db.seen.keys('nick'):
            nick, json_data = willie.db.seen.get(
                    row[0],  # We're getting back ('x',) when we need 'x'
                    ('nick', 'data'),
                    'nick'
                    )
            nn = Nick(nick)
            data = json.loads(unescape(json_data))
            time = data['time']
            assert type(time) is FloatType
            chan = data['channel']
            msg = data['message']
            r_tup = (time, chan, msg)
            willie.memory['seen'][nn.lower()] = r_tup
    finally:
        willie.memory['seen_lock'].release()


def seen_insert(willie, nick, data):
    # TODO change data imput to dict
    # TODO Just pass data through to databasae
    assert isinstance(nick, basestring)
    assert type(data) is TupleType
    assert len(data) == 3
    assert type(data[0]) is FloatType
    assert isinstance(data[1], basestring)
    assert isinstance(data[2], basestring)
    nn = Nick(nick)
    dict = {}
    dict['time'] = str(data[0])
    dict['channel'] = data[1]  # data[1] should be unicode
    dict['message'] = data[2]

    willie.memory['seen'][nn] = data
    #willie.debug('to insert', '%s, %r' % (nn.lower(), dict) ,'verbose')
    willie.db.seen.update(nn.lower(), {'data': escape(json.dumps(dict))})


'''
# TODO
#def seen_delete()
    willie.memory['seen_lock'].acquire()
    try:
    finally:
        willie.memory['seen_lock'].release()

# TODO
#def seen_ignore()
    willie.memory['seen_lock'].acquire()
    try:
    finally:
        willie.memory['seen_lock'].release()
'''

def load_from_logs(willie, trigger):
    if trigger.owner:
        willie.reply("Alright, I'll start looking through the logs, " +
                "but this is going to take a while...")
        willie.memory['seen_lock'].acquire()
        try:
            willie.debug('load_from_logs','='*25,'verbose')
            willie.debug('load_from_logs','Starting','verbose')
            filelist = []
            for f in os.listdir(log_dir):
                if log_regex.match(f) and os.path.isfile(log_dir + f):
                    filelist.append(log_dir + f)
            filelist.sort()
            for log in filelist:
                willie.debug(
                        '%f load_from_logs' % time(),
                        'opening %s' % log,
                        'verbose'
                        )
                with open(log, 'r') as file:
                    file_list = []
                    for l in file:
                        # omfg took me way too long to figure out 'replace'
                        file_list.append(l.decode('utf-8', 'replace'))
                    willie.debug(
                            '%f' % time(),
                            'finished loading file',
                            'verbose'
                            )
                    for line in file_list:
                        #line = line.decode('utf-8', 'replace')
                        #willie.debug('load_from_logs: line', line,'verbose')
                        willie.debug('%f' % time(), 'checking line', 'verbose')
                        m = line_regex.search(line)
                        if m:
                            '''willie.debug(
                                    'load_from_logs',
                                    'line is message',
                                    'verbose'
                                    )'''
                            '''willie.debug(
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
                                    os.path.basename(log))
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
                            utc_dt=cen.normalize(cen.localize(dt))
                            timestamp = float(utc_dt.strftime('%s'))
                            '''willie.debug(
                                    'logname',
                                    'utc timestamp is %f' % timestamp,
                                    'verbose'
                                    )'''
                            data = (timestamp, chan, msg)
                            willie.debug('%f' % time(), 'inserting', 'verbose')
                            seen_insert(willie, nn.lower(), data)
                            willie.debug('%f' % time(), 'inserted','verbose')
        finally:
            willie.memory['seen_lock'].release()
        willie.debug('','done','verbose')
        willie.reply("Okay, I'm done reading the logs!")
load_from_logs.commands = ['seen_load_logs']


def seen_nuke(willie, trigger):
    '''ADMIN: Nuke the seen database'''
    if trigger.owner:
        willie.reply("[](/ppsalute) Aye aye, nuking it from orbit.")
        willie.memory['seen_lock'].acquire()
        try:
            willie.memory['seen'] = {}  # NUKE IT FROM ORBIT
            for row in willie.db.seen.keys('nick'):
                willie.db.seen.delete(row[0], 'nick')
            willie.reply("Done!")
        finally:
            willie.memory['seen_lock'].release()
    else:
        willie.debug(
                'seen.py:nuke',
                '%s just tried to use the !nuke command!' % trigger.nick,
                'always'
                )
seen_nuke.commands = ['nuke']
seen_nuke.priority='low'


def seen_recorder(willie, trigger):
    if not trigger.args[0].startswith(u'#'):
        return  #ignore priv msg
    nn = Nick(trigger.nick)
    now = time()
    msg = trigger.args[1].strip().decode('utf-8', 'replace')
    willie.debug('raw message', type(msg), 'verbose')
    willie.debug('raw message', msg, 'verbose')
    chan = trigger.args[0].decode('utf-8', 'replace')

    data = (now, chan, msg)

    willie.memory['seen_lock'].acquire()
    try:
        seen_insert(willie, nn.lower(), data)
    finally:
        willie.memory['seen_lock'].release()
seen_recorder.priority='low'
seen_recorder.rule = '.*'


def seen(willie, trigger):
    '''Reports the last time a nick was seen.'''
    willie.debug('seen:seen', 'triggered custom module', 'verbose')
    if len(trigger.args[1].split()) == 1:
        willie.reply("Seen who?")
        return
    nn = Nick(trigger.args[1].split()[1])
    chan = trigger.args[0]

    willie.memory['seen_lock'].acquire()
    try:
        if nn in willie.memory['seen']:
            last = willie.memory['seen'][nn][0]
            chan = willie.memory['seen'][nn][1]
            msg = willie.memory['seen'][nn][2]

            td = timedelta(seconds=(time() - float(last)))
            if td.total_seconds() < (60):
                    t = 'less than a minute ago'
            elif td.total_seconds() < (3600):
                min = td.total_seconds() / 60
                if min != 1:
                    t = '%i minutes ago' % min
                else:
                    t = '1 minute ago'
            elif td.total_seconds() < (60*60*48):
                hr = td.total_seconds() / 60 / 60
                if hr != 1:
                    t = '%i hours ago' % hr
                else:
                    t = 'about an hour ago' % hr
            else:
                dt = datetime.utcfromtimestamp(last)
                f_datetime = dt.strftime('%b %d, %Y at %H:%M')
                t = 'on %s UTC ' % f_datetime
            willie.reply('I last saw %s in %s %s saying, "%s"' % (
                    colors.colorize(nn, ['purple']),
                    chan,
                    t,
                    colors.colorize(msg, ['navy'])
                    ))
            return
        else:
            willie.reply("I've not seen '%s'." % nn)
    finally:
        willie.memory['seen_lock'].release()
seen.commands = ['seen']
seen.example = '!seen tdreyer1'


if __name__ == "__main__":
    print __doc__.strip()
