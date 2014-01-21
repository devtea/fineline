"""
nicks.py - A Willie module providing Nick awareness for channels
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

from willie.tools import Nick
from willie.module import rule, event, commands, unblockable, thread, priority
import threading
import re


class NickPlus(Nick):
    _hostname = None

    def __new__(cls, nick, host):
        s = super(NickPlus, cls).__new__(cls, nick)
        s.hostname = host
        return s

    def hostname(self):
        return self._hostname

    def __eq__(self, other):
        if isinstance(other, NickPlus):
            return self._lowered == other._lowered or self.hostname == other.hostname
        return self._lowered == Nick._lower(other)


@commands(u'test')
def setup(bot):
    # bot.memory['chan_nicks']['#channel_name'] = [list, of, nicks]
    #               ^ dict          ^dict
    if 'chan_nicks' not in bot.memory:
        bot.memory['chan_nicks'] = {}
    if 'nick_lock' not in bot.memory:
        bot.memory['nick_lock'] = threading.Lock()
    if 'nick_func' not in bot.memory:
        def shared_nicks(channel, nick=None):
            if not nick and channel in bot.memory['chan_nicks']:
                return bot.memory['chan_nicks'][channel]
            elif nick and channel in bot.memory['chan_nicks']:
                return nick in bot.memory['chan_nicks'][channel]
            return None
        bot.memory['nick_func'] = shared_nicks
    # The documentation disagrees, but coretasks.py seems to be keeping
    # bot.channels up to date with joins, parts, kicks, etc.
    for chan in bot.channels:
        bot.write(['NAMES', chan])


@commands('list')
def list_nicks(bot, trigger):
    for i in bot.memory['chan_nicks']:
        print '%s: %r' % (i, bot.memory['chan_nicks'][i])


#@rule(u'.*353.*=.#.*:(.*)')
@rule('.*')
@event('353')
@unblockable
@thread(False)
@priority('high')
def names(bot, trigger):
    bot.debug(u'nicks.py', u'Caught NAMES response', u'verbose')
    # see https://github.com/embolalia/willie/blob/master/willie/coretasks.py
    try:
        unprocessed_nicks = re.split(' ', trigger)
        #TODO I have a feeling this needs to be nickplus with hostname
        nicks = [Nick(i) for i in unprocessed_nicks]
        channel = re.findall('#\S*', bot.raw)[0]  # bot.raw is undocumented but seems to be the raw line received
        bot.memory['chan_nicks'][channel] = nicks
    except:
        bot.debug(u'nicks.py:NAMES',
                  u'ERROR: Unprocessable NAMES response: %s' % bot.raw,
                  u'always'
                  )


@rule(u'.*')
@event('JOIN')
@unblockable
@thread(False)
@priority('high')
def join(bot, trigger):
    list_nicks(bot, trigger)
    bot.debug(u'nicks.py', u'Caught JOIN by %s' % trigger.nick, u'verbose')
    name = NickPlus(trigger.nick, trigger.host)
    if not trigger.sender.startswith('#'):
        return
    with bot.memory['nick_lock']:
        try:
            if name == bot.nick:
                # coretasks should take care of adding channel and NAMES
                pass
            else:
                bot.memory['chan_nicks'][trigger.sender].append(name)
        except:
            bot.debug(u'nicks.py:JOIN', u'ERROR: bot nick list is unsynced from server', u'always')
    list_nicks(bot, trigger)


@rule(u'.*')
@event('QUIT')
@unblockable
@thread(False)
@priority('high')
def quit(bot, trigger):
    list_nicks(bot, trigger)
    bot.debug(u'nicks.py', u'Caught QUIT by %s' % trigger.nick, u'verbose')
    name = NickPlus(trigger.nick, trigger.host)
    if not trigger.sender.startswith('#'):
        return
    with bot.memory['nick_lock']:
        try:
            if name == bot.nick:
                bot.memory['chan_nicks'].pop(trigger.sender, None)
            else:
                bot.memory['chan_nicks'][trigger.sender].remove(name)
        except:
            bot.debug(u'nicks.py:QUIT', u'ERROR: bot nick list is unsynced from server', u'always')
    list_nicks(bot, trigger)


@rule(u'.*')
@event('KICK')
@unblockable
@thread(False)
@priority('high')
def kick(bot, trigger):
    list_nicks(bot, trigger)
    bot.debug(u'nicks.py', u'Caught KICK by %s' % trigger.nick, u'verbose')
    name = NickPlus(trigger.nick, trigger.host)
    if not trigger.sender.startswith('#'):
        return
    with bot.memory['nick_lock']:
        try:
            if trigger.nick == bot.nick:
                bot.memory['chan_nicks'].pop(trigger.sender, None)
            else:
                bot.memory['chan_nicks'][trigger.sender].remove(name)
        except:
            bot.debug(u'nicks.py:KICK', u'ERROR: bot nick list is unsynced from server', u'always')
    list_nicks(bot, trigger)


@rule(u'.*')
@event('PART')
@unblockable
@thread(False)
@priority('high')
def part(bot, trigger):
    list_nicks(bot, trigger)
    bot.debug(u'nicks.py', u'Caught PART by %s' % trigger.nick, u'verbose')
    name = NickPlus(trigger.nick, trigger.host)
    if not trigger.sender.startswith('#'):
        return
    with bot.memory['nick_lock']:
        try:
            if trigger.nick == bot.nick:
                bot.memory['chan_nicks'].pop(trigger.sender, None)
            else:
                bot.memory['chan_nicks'][trigger.sender].remove(name)
        except:
            bot.debug(u'nicks.py:PART', u'ERROR: bot nick list is unsynced from server', u'always')
    list_nicks(bot, trigger)


@rule(u'.*')
@event('NICK')
@unblockable
@thread(False)
@priority('high')
def nick(bot, trigger):
    list_nicks(bot, trigger)
    bot.debug(u'nicks.py', u'Caught NICK by %s' % trigger.nick, u'verbose')
    # Trigger doesn't come from channel. Any replies will be sent to user
    name = NickPlus(trigger.nick, trigger.host)
    new_name = Nick(trigger, trigger.host)
    with bot.memory['nick_lock']:
        for chan in bot.memory['chan_nicks']:
            try:
                if name in bot.memory['chan_nicks'][chan]:
                    bot.memory['chan_nicks'][chan].remove(name)
                    bot.memory['chan_nicks'][chan].append(new_name)
            except:
                bot.debug(u'nicks.py:NICK', u'ERROR: bot nick list is unsynced from server', u'always')
    list_nicks(bot, trigger)


if __name__ == "__main__":
    print __doc__.strip()
