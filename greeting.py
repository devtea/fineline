"""
greeting.py - A Willie module that greets newcomers to a channel
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from willie.module import commands, rule, event, unblockable, priority
import threading
import gzip
import re
import os
import time

from willie.tools import Nick

_re_loglines = re.compile(r'\[[0-9:]*]\s\*{3}\sJoins:\s(\S+)\s\(([^)]+)\)')
_chan_regex = re.compile(u'^(.*?)_\d{8}')

# Bot framework is stupid about importing, so we need to override so that
# these modules are always available for import.
try:
    import nicks
except:
    import imp
    import sys
    try:
        print "trying manual import of nicks"
        fp, pathname, description = imp.find_module('nicks', ['./.willie/modules/'])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()


def logtime():
    # A quick time formatting function return time formatted for logs.
    return unicode(time.strftime('%Y%m%d %H:%M:%S UTC', time.gmtime()))


def configure(config):
    '''
    [ Greeting ]
    -----------
    | logs | /var/logs/irc/#linux,/var/logs/irc/#windows | List of log locations to parse |
    '''
    if config.option('Configure the log locations for the greeting module?', False):
        config.add_section('greeting')
        config.add_list('greeting', 'logs', "What locations are the logs contained in", "Full log directory path:")
        config.interactive_add('greeting', 'name_regex', "What regex will match log files", default='.*')


def setup(bot):
    if not (bot.config.has_option('greeting', 'logs')
            and bot.config.greeting.get_list('logs')
            and bot.config.has_option('greeting', 'name_regex')
            and bot.config.greeting.name_regex
            ):
        return
    if 'greet_lock' not in bot.memory:
        bot.memory['greet_lock'] = threading.Lock()
    with bot.memory['greet_lock']:
        bot.memory['chan_host_hist'] = {}
        if 'greet' not in bot.memory:
            bot.memory['greet'] = {}
        bot.memory['greet']['ings'] = {}
        if 'logs' not in bot.memory['greet']:
            bot.memory['greet']['logs'] = bot.config.greeting.get_list('logs')
        if 'log_regex' not in bot.memory['greet']:
            bot.memory['greet']['log_regex'] = re.compile(bot.config.greeting.name_regex)
        db = bot.db.connect()
        cur = db.cursor()
        hist_query = None
        greet_query = None
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS chan_host_hist
                           (channel text, nick text, host text)''')
            db.commit()
            cur.execute('SELECT channel, nick, host FROM chan_host_hist')
            hist_query = cur.fetchall()

            cur.execute('''CREATE TABLE IF NOT EXISTS greetings
                           (channel text, notice text, greeting text)''')
            db.commit()
            cur.execute('select channel, notice, greeting from greetings')
            greet_query = cur.fetchall()
        finally:
            cur.close()
            db.close()
        if hist_query:
            for c, n, h in hist_query:
                if c not in bot.memory['chan_host_hist']:
                    bot.memory['chan_host_hist'][c] = []
                bot.memory['chan_host_hist'][c].append(nicks.NickPlus(n, h))
        if greet_query:
            for c, n, m in greet_query:
                if c not in bot.memory['greet']['ings']:
                    bot.memory['greet']['ings'][c] = (n, m)


@commands(u'greeting_initialize')
def greeting_initialize(bot, trigger):
    if not trigger.owner:
        return
    tmp_hostlist = {}

    def parse_log(channel, log_file):
        file_list = []
        for l in log_file:
            file_list.append(l.decode('utf-8', 'replace'))  # omfg took me way too long to figure out 'replace'
        bot.debug(logtime(), u'finished loading file', u'verbose')
        for line in file_list:
            nicknhost = _re_loglines.search(line)
            if nicknhost:
                nn, host = nicknhost.groups()
                nn = Nick(nn)
                host = host.lstrip('~')
                bot.debug(logtime(), u'found nick and host. %s %s for %s' % (nn, host, channel), u'verbose')
                if channel not in tmp_hostlist:
                    tmp_hostlist[channel] = {}
                if nn not in tmp_hostlist[channel]:
                    tmp_hostlist[channel][nn] = []
                if host not in tmp_hostlist[channel][nn]:
                    tmp_hostlist[channel][nn].append(host)

    bot.reply(u"Okay, I'll start looking through the logs, but this may take a while.")
    with bot.memory['greet_lock']:
        bot.debug(logtime(), u'=' * 25, u'verbose')
        bot.debug(logtime(), u'Starting', u'verbose')
        filelist = []
        # Parse provided log files for nicks and hostnames. ZNC Default logs
        for dir in bot.memory['greet']['logs']:
            for f in os.listdir(dir):
                if bot.memory['greet']['log_regex'].match(f) and os.path.isfile(dir + f):
                    filelist.append(dir + f)
        for log in filelist:
            bot.debug(logtime(), u'opening %s' % log, u'verbose')
            log_name = os.path.splitext(os.path.basename(log))
            bot.debug(logtime(), u'logname %s' % log_name[0], u'verbose')
            chan = _chan_regex.search(log_name[0]).groups()[0].decode('utf-8', 'replace')
            if log.endswith('gz'):
                with gzip.open(log, 'rb') as gfile:  # May need to switch to r if problems
                    parse_log(chan, gfile)
            else:
                with open(log, 'r') as rfile:
                    parse_log(chan, rfile)
        # Add everyone in joined rooms to list
        for channel in bot.channels:
            if channel not in tmp_hostlist:
                tmp_hostlist[channel] = {}
            for n in nicks.in_chan(bot, channel):
                if n not in tmp_hostlist[channel]:
                    tmp_hostlist[channel][n] = []
                if n.hostname not in tmp_hostlist[channel][n]:
                    tmp_hostlist[channel][n].append(n.hostname)

        for channel in tmp_hostlist:
            chans_nicks = [nicks.NickPlus(n, h) for n in tmp_hostlist[channel] for h in tmp_hostlist[channel][n]]
            bot.memory['chan_host_hist'][channel] = chans_nicks
            db = bot.db.connect()
            cur = db.cursor()
            insert = [(channel, n, n.hostname) for n in chans_nicks]
            try:
                cur.executemany('''insert into chan_host_hist (channel, nick, host)
                                values (?, ?, ?)''', insert)
                db.commit()
            finally:
                cur.close()
                db.close()
    bot.debug(logtime(), u'done loading from logs!', u'verbose')
    bot.reply(u"Okay, I'm done reading the logs! ^_^")


@commands('greet_nuke')
def greet_nuke(bot, trigger):
    '''ADMIN: Nuke the greeting database'''
    if trigger.owner:
        bot.reply(u"[](/ppsalute) Aye aye, nuking it from orbit.")
        with bot.memory['greet_lock']:
            bot.memory['chan_host_hist'] = {}
            db = bot.db.connect()
            cur = db.cursor()
            try:
                cur.execute('delete from chan_host_hist')
                db.commit()
            finally:
                cur.close()
                db.close()
        bot.reply(u"Done!")
    else:
        bot.debug(logtime(), u'%s(%s) just tried to use the !nuke command!' % (trigger.nick, trigger.host), u'always')


@commands(u'greet_dump')
def greet_dump(bot, trigger):
    '''ADMIN: a debug dump the chan_host_history database'''
    if not trigger.owner:
        return
    with bot.memory['greet_lock']:
        bot.say(u'Dumping to logs.')
        for channel in bot.memory['chan_host_hist']:
            bot.debug(u'greet dump', u'Channel: %s' % channel, u'always')
            for nick in bot.memory['chan_host_hist'][channel]:
                bot.debug(u'greet dump', u'Nick: %s | Host: %s' % (nick, nick.hostname), u'always')
        bot.say(u'Done.')


@rule(u'.*')
@event('JOIN')
@unblockable
@priority('low')
def join_watcher(bot, trigger):
    if not trigger.sender.startswith('#'):
        return
    with bot.memory['greet_lock']:
        try:
            nick = nicks.NickPlus(trigger.nick, trigger.host.lstrip('~'))
            if trigger.sender not in bot.memory['chan_host_hist']:
                bot.memory['chan_host_hist'][trigger.sender] = []
            if nick not in bot.memory['chan_host_hist'][trigger.sender]:
                bot.memory['chan_host_hist'][trigger.sender].append(nick)
                db = bot.db.connect()
                cur = db.cursor()
                try:
                    cur.execute('''insert into chan_host_hist (channel, nick, host)
                                    values (?, ?, ?)''', (trigger.sender, nick, nick.hostname))
                    db.commit()
                finally:
                    cur.close()
                    db.close()
                channel = trigger.sender.lower()
                print 'testing if greeting'
                if channel in bot.memory['greet']['ings']:
                    # This is where joiners actually get greeted
                    print 'found greeting testing notice'
                    print bot.memory['greet']['ings'][channel][0]
                    if bot.memory['greet']['ings'][channel][0] == 'n':
                        print "MESSAGE send: %s | msg: %s" % (trigger.sender, bot.memory['greet']['ings'][channel][1])
                        bot.msg(trigger.sender, u'%s: %s' % (trigger.nick, bot.memory['greet']['ings'][channel][1]))
                    else:
                        print "NOTICE send: %s | msg: %s" % (trigger.nick, bot.memory['greet']['ings'][channel][1])
                        bot.write(['NOTICE', trigger.nick], '%s: %s' % (trigger.nick, bot.memory['greet']['ings'][channel][1]))
        except:
            bot.debug(logtime(), u'[greeting] Unhandled exception in hostname watcher! %s [%s]' % (sys.exc_info()[0], trigger.bytes), u'always')


@commands('greet_add', 'greeting_add')
def greeting_add(bot, trigger):
    '''ADMIN: Add greetings for channels. Syntax: Channel Notice(y/n) Greeting to say'''
    if not trigger.owner:
        return
    try:
        triggers = trigger.split()[1:]
        print triggers
        channel = triggers.pop(0).lower()
        notice = triggers.pop(0).lower()
        message = u' '.join(triggers)
    except IndexError:
        bot.reply(u'Malformed input. Takes 3 arguments, channel, notice(y/n), and message.')
        return
    if not message:
        bot.reply(u'Malformed input. Takes 3 arguments, channel, notice(y/n), and message.')
        return
    if notice not in ['y', 'n']:
        bot.reply(u'Notice must be either "Y" or "N".')
        return
    with bot.memory['greet_lock']:
        if channel in bot.memory['greet']['ings']:
            bot.reply(u'That channel already has a greeting')
            bot.say(u'%s: %s' % (channel, bot.memory['greet']['ings'][channel][1]))
            return
        else:
            db = bot.db.connect()
            cur = db.cursor()
            try:
                cur.execute('''insert into greetings (channel, notice, greeting)
                            values (?, ?, ?)''', (channel, notice, message))
                db.commit()
            finally:
                cur.close()
                db.close()
            bot.memory['greet']['ings'][channel] = (notice, message)
            bot.say('Greeting added.')


@commands('greet_del', 'greeting_del')
def greeting_del(bot, trigger):
    '''ADMIN: Removes greetings for channels. Syntax = #Channel'''
    if not trigger.owner:
        return
    triggers = trigger.split()[1:]
    if len(triggers) > 1:
        bot.reply(u'Malformed input. Takes only 1 argument: channel')
        return
    elif len(triggers) == 1:
        channel = triggers[0].lower()
    else:
        channel = trigger.sender
    with bot.memory['greet_lock']:
        if channel not in bot.memory['greet']['ings']:
            bot.reply(u'%s has no greeting.' % channel)
        else:
            db = bot.db.connect()
            cur = db.cursor()
            try:
                cur.execute('delete from greetings where channel = ?', (channel,))
                db.commit()
            finally:
                cur.close()
                db.close()
            del bot.memory['greet']['ings'][channel]
            bot.reply(u'Greeting removed from %s' % channel)


@commands('greet_list', 'greeting_list')
def greeting_list(bot, trigger):
    '''ADMIN: Lists greeting for a channel.'''
    if not trigger.owner:
        return
    triggers = trigger.split()[1:]
    print triggers
    if len(triggers) > 1:
        bot.reply(u'Malformed input. Takes only 1 argument: channel')
        return
    elif len(triggers) == 1:
        channel = triggers[0].lower()
    else:
        channel = trigger.sender
    with bot.memory['greet_lock']:
        if channel not in bot.memory['greet']['ings']:
            bot.say('%s does not have a greeting.' % channel)
            return
        notice, message = bot.memory['greet']['ings'][channel]
        if notice == 'y':
            notice = 'NOTICE'
        else:
            notice = 'Message'
        bot.say(u'%s has a %s greeting of "%s"' % (channel, notice, message))


if __name__ == "__main__":
    print __doc__.strip()
