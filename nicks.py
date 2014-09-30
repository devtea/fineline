"""
nicks.py - A Willie module providing Nick awareness for channels
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
# An important note about dealing with NickPluses. Simple == comparisons can
# cause weird results due to hostname matching. If you are doing an action to a
# nick, removing a nick, or otherwise doing anything where you *don't* want
# hostname matching to cause issues, explicitly use the .lower() method in your
# comparison.
from __future__ import print_function

import os.path
import re
import threading
import time
import traceback


from willie.tools import Nick
from willie.module import rule, event, commands, unblockable, thread, priority

re_hostname = re.compile(r':\S+\s311\s\S+\s(\S+)\s\S+\s(\S+)\s\*')

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        print("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()


class NickPlus(Nick):
    _hostname = None

    def __new__(cls, nick, host=None):
        s = Nick.__new__(cls, nick)
        s.hostname = host
        return s

    def hostname(self):
        return self._hostname

    def __eq__(self, other):
        if isinstance(other, NickPlus) and \
                (self.hostname is not None) and (other.hostname is not None):
            return self._lowered == other._lowered or self.hostname == other.hostname
        return self._lowered == Nick._lower(other)

    def __hash__(self):
        return 0  # Fuck the police


# def shared_nicks(channel, nick=None):
def in_chan(bot, channel, nick=None):
    if not nick and channel in bot.memory['chan_nicks']:
        return bot.memory['chan_nicks'][channel]
    elif nick and channel in bot.memory['chan_nicks']:
        return nick in bot.memory['chan_nicks'][channel]
    return None


def setup(bot):
    # bot.memory['chan_nicks']['#channel_name'] = [list, of, nicks]
    #               ^ dict          ^dict
    bot.memory['chan_nicks'] = {}
    if 'nick_lock' not in bot.memory:
        bot.memory['nick_lock'] = threading.Lock()
    if 'whois_lock' not in bot.memory:
        bot.memory['whois_lock'] = threading.Lock()
    bot.memory['whois_time'] = {}
    refresh_nicks(bot)


def refresh_nicks(bot):
    # The documentation disagrees, but coretasks.py seems to be keeping
    # bot.channels up to date with joins, parts, kicks, etc.
    for chan in bot.channels:
        with bot.memory['nick_lock']:
            bot.memory['chan_nicks'][chan] = {}
            bot.write(['NAMES', chan])
        time.sleep(0.5)


@commands('nick_list')
def list_nicks(bot, trigger):
    '''Prints nick module debugging info to the log. Admin only.'''
    if not trigger.owner and not trigger.admin and not trigger.isop:
        return
    for i in bot.memory['chan_nicks']:
        try:
            print('%s: %r' % (i, [(n, n.hostname) for n in bot.memory['chan_nicks'][i]]))
        except:
            print('%s: %r' % (i, bot.memory['chan_nicks'][i]))


@rule('.*')
@event('311')
@unblockable
@priority('high')
@thread(False)  # Don't remove this or you'll break the bot.raw call
def whois_catcher(bot, trigger):
    bot.debug(__file__, log.format(u'Caught WHOIS response'), u'verbose')
    n, h = re_hostname.search(bot.raw).groups()
    who = NickPlus(n.lstrip('+%@&~'), h)
    with bot.memory['nick_lock']:
        for chan in bot.memory['chan_nicks']:
            # Replace all matching nicks with the updated nick from the whois
            # query, but only if the existing doesn't have a hostname. This is
            # to prevent the possibility of someone NICKing before the whois
            # gets processed and getting the new nick overwritten with the old.
            bot.memory['chan_nicks'][chan] = \
                [who if i.lower() == who.lower() and i.hostname is None else i for i in bot.memory['chan_nicks'][chan]]


@rule('.*')
@event('353')
@unblockable
@priority('high')
@thread(False)  # Don't remove this or you'll break the bot.raw call
def names(bot, trigger):
    buf = bot.raw.strip()  # bot.raw is undocumented but seems to be the raw line received
    bot.debug(__file__, log.format(u'Caught NAMES response'), u'verbose')
    try:
        with bot.memory['nick_lock']:
            bot.debug(__file__, log.format('trigger:', trigger), 'verbose')
            unprocessed_nicks = re.split(' ', trigger)
            stripped_nicks = [i.lstrip('+%@&~') for i in unprocessed_nicks]
            nicks = [NickPlus(i, None) for i in stripped_nicks]
            channel = re.findall('#\S*', buf)[0]
            if not channel:
                return
            bot.memory['chan_nicks'][channel] = nicks
        bot.debug(__file__, log.format(u'Refeshing hosts for ', channel), 'verbose')
        for n in nicks:
            with bot.memory['whois_lock']:
                # Prevent whoising the same nick multiple times across threads (for a short time)
                if n not in bot.memory['whois_time'] or bot.memory['whois_time'][n] < time.time() - 600:
                    bot.memory['whois_time'][n] = time.time()
                    bot.write(['WHOIS', n.lower()])
                    time.sleep(0.5)  # This keeps our aggregate whois rate reasonable
            # time.sleep(3)  # Wait a bit for other threads to spam whoissses too
        bot.debug(__file__, log.format(u'Done refeshing hosts for ', channel), 'verbose')
    except:
        bot.debug(__file__, log.format(u'ERROR: Unprocessable NAMES response: ', buf), u'always')
        print(traceback.format_exc())


@rule(u'.*')
@event('JOIN')
@unblockable
@thread(False)
@priority('high')
def join(bot, trigger):
    # list_nicks(bot, trigger)
    bot.debug(__file__, log.format(u'Caught JOIN by ', trigger.nick), u'verbose')
    try:
        name = NickPlus(trigger.nick, trigger.host)
        if not trigger.sender.startswith('#'):
            return
        with bot.memory['nick_lock']:
            # Coretasks should take care of adding channel and NAMES so we take
            # care of everyone else
            if name != bot.nick:
                bot.memory['chan_nicks'][trigger.sender].append(name)
    # list_nicks(bot, trigger)
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'always')
        print(traceback.format_exc())
        refresh_nicks(bot)


@rule(u'.*')
@event('NICK')
@unblockable
@thread(False)
@priority('high')
def nick(bot, trigger):
    # list_nicks(bot, trigger)
    bot.debug(__file__, log.format(u'Caught NICK by %s >> %s' % (trigger.nick, trigger)), u'verbose')
    # Trigger doesn't come from channel. Any replies will be sent to user.
    # Old nick is in trigger.nick while new nick is in trigger and
    # trigger.sender
    try:
        old_nick = NickPlus(trigger.nick, trigger.host)
        new_nick = NickPlus(trigger, trigger.host)
        with bot.memory['nick_lock']:
            for chan in bot.memory['chan_nicks']:
                bot.memory['chan_nicks'][chan] = \
                    [new_nick if old_nick.lower() == i.lower() else i for i in bot.memory['chan_nicks'][chan]]
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'always')
        print(traceback.format_exc())
        refresh_nicks(bot)


@rule(u'.*')
@event('QUIT')
@unblockable
@thread(False)
@priority('high')
def quit(bot, trigger):
    # list_nicks(bot, trigger)
    bot.debug(__file__, log.format(u'Caught QUIT by ', trigger.nick), u'verbose')
    try:
        name = NickPlus(trigger.nick, trigger.host)
        if not trigger.sender.startswith('#'):
            return
        with bot.memory['nick_lock']:
            for chan in bot.memory['chan_nicks']:
                try:
                    # Use a Nick() so hostname don't fuck it up
                    bot.memory['chan_nicks'][chan].remove(Nick(name.lower()))
                except:
                    # Didn't find nick in channel
                    bot.debug(__file__, log.format(u'Didn\'t find %s in %s to remove.' % (name, chan)), 'verbose')
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'always')
        print(traceback.format_exc())
        refresh_nicks(bot)


@rule(u'.*')
@event('KICK')
@unblockable
@thread(False)
@priority('high')
def kick(bot, trigger):
    # list_nicks(bot, trigger)
    bot.debug(__file__, log.format(u'Caught KICK by ', trigger.nick), u'verbose')
    try:
        name = Nick(trigger)  # Trigger comes in as trigger==kicked, trigger.nick==kicker
        if not trigger.sender.startswith('#'):
            return
        with bot.memory['nick_lock']:
                if trigger == bot.nick:
                    bot.memory['chan_nicks'].pop(trigger.sender, None)
                else:
                    # Use a Nick() so hostname don't fuck it up
                    bot.memory['chan_nicks'][trigger.sender].remove(Nick(name.lower()))
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'always')
        print(traceback.format_exc())
        refresh_nicks(bot)


@rule(u'.*')
@event('PART')
@unblockable
@thread(False)
@priority('high')
def part(bot, trigger):
    # list_nicks(bot, trigger)
    bot.debug(__file__, log.format(u'Caught PART by ', trigger.nick), u'verbose')
    try:
        name = NickPlus(trigger.nick, trigger.host)
        if not trigger.sender.startswith('#'):
            return
        with bot.memory['nick_lock']:
                if trigger.nick == bot.nick:
                    bot.memory['chan_nicks'].pop(trigger.sender, None)
                else:
                    # Use a Nick() so hostname don't fuck it up
                    bot.memory['chan_nicks'][trigger.sender].remove(Nick(name.lower()))
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'always')
        print(traceback.format_exc())
        refresh_nicks(bot)


if __name__ == "__main__":
    print(__doc__.strip())
