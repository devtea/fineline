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


from willie.tools import Identifier
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

    @property
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, value):
        assert isinstance(value, basestring) or value is None
        self._hostname = value

    def __eq__(self, other):
        if isinstance(other, NickPlus) and \
                (self.hostname is not None) and (other.hostname is not None):
            return self._lowered == other._lowered or self.hostname == other.hostname
        return self._lowered == Nick._lower(other)

    def __hash__(self):
        return 0  # Fuck the police

    def __repr__(self):
        return '%s(%s - %s)' % (self.__class__.__name__, self.__str__(), self._hostname)


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
            print('%s: %r' % (i, [n for n in bot.memory['chan_nicks'][i]]))
        except:
            print('%s: %r' % (i, bot.memory['chan_nicks'][i]))


@rule('.*')
@event('311')
@unblockable
@priority('high')
@thread(False)  # Don't remove this or you'll break the bot.raw call
def whois_catcher(bot, trigger):
    '''Parses whois responses'''
    n, h = re_hostname.search(bot.raw).groups()
    who = NickPlus(n.lstrip('+%@&~'), h)
    bot.debug(__file__, log.format(u'WHOIS %s: %s' % (who, h)), u'verbose')
    with bot.memory['nick_lock']:
        for chan in bot.memory['chan_nicks']:
            # Replace all matching nicks with the updated nick from the whois
            # query, but only if the existing doesn't have a hostname. This is
            # to prevent the possibility of someone NICKing before the whois
            # gets processed and getting the new nick overwritten with the old.
            bot.memory['chan_nicks'][chan] = \
                [who if i.lower() == who.lower() and i.hostname is None else i for i in bot.memory['chan_nicks'][chan]]


@rule(u'.*')
@event('353')
@unblockable
@priority('high')
@thread(False)  # Don't remove this or you'll break the bot.raw call
def names(bot, trigger):
    '''Parses NAMES responses from the server which happen on joining a channel'''
    # Freenode example:
    # <<1412452815.61 :card.freenode.net 353 botname = #channelname :botname +nick1 nick2 nick3 nick_4
    buf = bot.raw.strip()  # bot.raw is undocumented but seems to be the raw line received
    bot.debug(__file__, log.format(u'Caught NAMES response'), u'verbose')
    try:
        with bot.memory['nick_lock']:
            bot.debug(__file__, log.format('trigger:', trigger), 'verbose')
            unprocessed_nicks = re.split(' ', trigger)
            stripped_nicks = [i.lstrip('+%@&~') for i in unprocessed_nicks]
            bot.debug(__file__, [i for i in stripped_nicks], u'verbose')
            nicks = [NickPlus(i, None) for i in stripped_nicks]
            channel = re.findall('#\S*', buf)[0]
            if not channel:
                return
            if channel not in bot.memory['chan_nicks']:
                bot.memory['chan_nicks'][channel] = []
            bot.memory['chan_nicks'][channel].extend(nicks)
            bot.debug(__file__, log.format(u'Refeshing hosts for ', channel), 'verbose')
            for n in nicks:
                if n not in bot.memory['whois_time'] or bot.memory['whois_time'][n] < time.time() - 600:
                    # Send the server a whois query if we haven't gotten one
                    # yet/recently
                    bot.memory['whois_time'][n] = time.time()
                    bot.write(['WHOIS', n])
                    time.sleep(0.5)  # This keeps our aggregate whois rate reasonable
                else:
                    # If the nick has been recently WHOIS'd just use that one
                    # so we don't spam the server
                    for chan in bot.memory['chan_nicks']:
                        match = next((nick for nick in bot.memory['chan_nicks'][chan] if nick == n and nick.hostname), None)
                        if match:
                            bot.debug(__file__, log.format(u'Just matched %s to %r in place of a whois.' % (n, match)), 'verbose')
                            break
                    if match:
                        # This should never generate a value error since we just
                        # added it a few lines above
                        bot.memory['chan_nicks'][channel].remove(n)  # Remove the nick with None host
                        bot.memory['chan_nicks'][channel].append(match)  # Add nick with an actual host
                    else:
                        # Do nothing. If a nick wasn't matched then we haven't
                        # gotten the chance to process the appropriate whois
                        # response yet. That whois will come in and overwrite
                        # the entry with a None hostname.
                        pass

        bot.debug(__file__, log.format(u'Done refeshing hosts for ', channel), 'verbose')
    except:
        bot.debug(__file__, log.format(u'ERROR: Unprocessable NAMES response: ', buf), u'warning')
        print(traceback.format_exc())
        # refresh_nicks(bot)
        bot.msg(bot.config.owner, u'A name entry just broke. Check the logs for details.')


@rule(u'.*')
@event('JOIN')
@unblockable
@thread(False)
@priority('high')
def join(bot, trigger):
    bot.debug(__file__, log.format(u'Caught JOIN by ', trigger.nick), u'verbose')
    try:
        name = NickPlus(trigger.nick, trigger.host)
        if not trigger.sender.startswith('#'):
            return
        with bot.memory['nick_lock']:
            # Channel adding on bot join is taken care of in the NAMES
            # processing
            if name != bot.nick:
                if trigger.nick not in bot.memory['chan_nicks'][trigger.sender]:
                    bot.memory['chan_nicks'][trigger.sender].append(name)
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'warning')
        print(traceback.format_exc())
        # refresh_nicks(bot)
        bot.msg(bot.config.owner, u'A join by %s in %s just broke me. Check the logs for details.' % (trigger.nick, trigger.sender))


@rule(u'.*')
@event('NICK')
@unblockable
@thread(False)
@priority('high')
def nick(bot, trigger):
    bot.debug(__file__, log.format(u'Caught NICK by %s >> %s' % (trigger.nick, trigger)), u'verbose')
    # Trigger doesn't come from channel. Any replies will be sent to user.
    # Old nick is in trigger.nick while new nick is in trigger and
    # trigger.sender
    try:
        old_nick = trigger.nick
        new_nick = NickPlus(trigger, trigger.host)
        with bot.memory['nick_lock']:
            for chan in bot.memory['chan_nicks']:
                if old_nick in bot.memory['chan_nicks'][chan]:
                    bot.memory['chan_nicks'][chan].remove(old_nick)
                    bot.memory['chan_nicks'][chan].append(new_nick)
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'warning')
        print(traceback.format_exc())
        # refresh_nicks(bot)
        bot.msg(bot.config.owner, u'A nick by %s just broke me. Check the logs for details.' % trigger.nick)


@rule(u'.*')
@event('QUIT')
@unblockable
@thread(False)
@priority('high')
def quit(bot, trigger):
    bot.debug(__file__, log.format(u'Caught QUIT by %s (%s)' % (trigger.nick, trigger)), u'verbose')
    # Quitting nick is trigger.nick, trigger and trigger.sender contain quit
    # reason. Don't use trigger.sender to determine if the user is in a
    # channel!
    try:
        name = trigger.nick
        with bot.memory['nick_lock']:
            for chan in bot.memory['chan_nicks']:
                bot.debug(__file__, log.format(u'Looking for %s in %s' % (name, chan)), u'verbose')
                if name in bot.memory['chan_nicks'][chan]:
                    bot.debug(__file__, log.format(u'Found %s in %s to remove' % (name, chan)), u'verbose')
                    bot.memory['chan_nicks'][chan].remove(name)
                else:
                    bot.debug(__file__, log.format(u'%s not found in %s to remove' % (name, chan)), u'verbose')
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'warning')
        print(traceback.format_exc())
        bot.msg(bot.config.owner, u'A quit by %s just broke me. Check the logs for details.' % trigger.nick)


@rule(u'.*')
@event('KICK')
@unblockable
@thread(False)
@priority('high')
def kick(bot, trigger):
    # kicked = 4th part of bot.raw, kicker = trigger.nick, kick reason = trigger
    target = bot.raw.split()[3]
    bot.debug(
        __file__,
        log.format(u'Caught KICK of %s by %s in %s' % (
            target, trigger.nick, trigger.sender)),
        u'verbose')
    try:
        name = target
        if not trigger.sender.startswith('#'):
            return
        with bot.memory['nick_lock']:
            if name == bot.nick:
                bot.memory['chan_nicks'].pop(trigger.sender, None)
            else:
                bot.memory['chan_nicks'][trigger.sender].remove(name)
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'warning')
        print(traceback.format_exc())
        bot.msg(bot.config.owner, u'A kick of %s in %s just broke me. Check the logs for details.' % (name, trigger.sender))


@rule(u'.*')
@event('PART')
@unblockable
@thread(False)
@priority('high')
def part(bot, trigger):
    bot.debug(__file__, log.format(u'Caught PART by %s from %s' % (trigger.nick, trigger.sender)), u'verbose')
    try:
        name = trigger.nick  # Don't want to use a NickPlus because hostname matching
        if not trigger.sender.startswith('#'):
            return
        with bot.memory['nick_lock']:
                if trigger.nick == bot.nick:
                    bot.memory['chan_nicks'].pop(trigger.sender, None)  # The bot left the room.
                else:
                    try:
                        bot.memory['chan_nicks'][trigger.sender].remove(name)
                    except KeyError:
                        bot.debug(__file__, log.format('%s not found in nick list when they parted from %s.' % (name, trigger.sender)), 'warning')
    except:
        bot.debug(__file__, log.format(u'ERROR: bot nick list is unsynced from server'), u'warning')
        print(traceback.format_exc())
        bot.msg(bot.config.owner, u'A part in %s just broke me. Check the logs for details.' % trigger.sender)


if __name__ == "__main__":
    print(__doc__.strip())
