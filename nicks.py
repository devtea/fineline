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
import re
import threading
import time

from willie.logger import get_logger
from willie.module import rule, event, commands, unblockable, thread, priority
from willie.tools import Identifier

LOGGER = get_logger(__name__)

re_hostname = re.compile(r':\S+\s311\s\S+\s(\S+)\s\S+\s(\S+)\s\*')

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    import os.path
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()


class NickPlus(Identifier):
    _hostname = None

    def __new__(cls, nick, host=None):
        s = Identifier.__new__(cls, nick)
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
        return self._lowered == Identifier._lower(other)

    def __hash__(self):
        return 0  # Fuck the police

    def __repr__(self):
        return '%s(%s - %s)' % (self.__class__.__name__, self.__str__(), self._hostname)


def update_from_priv(bot):
    '''This should always be called from inside a lock.'''
    nlist = list(bot.memory['nicks'])
    priv = dict(bot.privileges)

    privlist = set([i for i in {n for c in priv.itervalues() for n in c}])  # Flatten the dict to a set of ids sans channels
    bot.memory['nicks'] = [i for i in nlist if i in privlist]  # Remove any nicks that aren't around anymore
    for i in [x for x in privlist if x not in bot.memory['nicks']]:  # Whois any nicks we didn't already have
        # Add first, then whois
        bot.memory['nicks'].append(NickPlus(i, None))
        whois(bot, i)


def whois(bot, identifier):
    '''Sends WHOIS commands to the server at sane intervals. Should only be
    referenced from inside a lock.'''
    time.sleep(0.5)
    bot.write(['WHOIS', identifier])


# def shared_nicks(channel, nick=None):
def in_chan(bot, channel, nick=None):
    '''Returns a list of NickPlus objects in the specified channel. If nick is provided,
    returns boolean of whether that object is in the channel.'''
    priv = dict(bot.privileges)
    with bot.memory['nick_lock']:
        if not nick and channel in priv.keys():
            tmp = [i for i in bot.memory['nicks'] if i in priv[channel].keys()]
            LOGGER.info(log.format(tmp))
            return tmp
        elif nick and channel in priv.keys():
            return nick in priv[channel].keys()
        return None


def setup(bot):
    # bot.memory['chan_nicks']['#channel_name'] = [list, of, nicks]
    #               ^ dict          ^dict
    #
    # New style, bot.memory['nicks'] = [list, of nicks]
    if 'nicks' not in bot.memory:
        bot.memory['nicks'] = []  # Tried to use a set here, but that fucks things up
    if 'nick_lock' not in bot.memory:
        bot.memory['nick_lock'] = threading.Lock()


@commands('nick_list')
def list_nicks(bot, trigger):
    '''Prints nick module debugging info to the log. Admin only.'''
    if not trigger.owner and not trigger.admin and not trigger.isop:
        return
    with bot.memory['nick_lock']:
        LOGGER.warning(log.format('=== Nick List ==='))
        for i in bot.memory['nicks']:
            LOGGER.warning(log.format('(%s) %s, %s'), type(i), i, i.hostname)


@rule('.*')
@event('311')
@unblockable
@priority('high')
def whois_catcher(bot, trigger):
    '''Parses whois responses'''
    try:
        # No more bot.raw in willie 5.0. trigger.raw seems usable
        n, h = re_hostname.search(trigger.raw).groups()
        who = NickPlus(n.lstrip('+%@&~'), h)
        LOGGER.info(log.format('Caught WHOIS %s: %s'), who, h)
        with bot.memory['nick_lock']:
            # Replace all matching nicks with the updated nick from the whois
            # query, but only if the existing doesn't have a hostname. This is
            # to prevent the possibility of someone NICKing before the whois
            # gets processed and getting the new nick overwritten with the old.
            # bot.memory['chan_nicks'][chan] = \
            #    [who if i.lower() == who.lower() and i.hostname is None else i for i in bot.memory['chan_nicks'][chan]]
            bot.memory['nicks'] = [who if i.lower() == who.lower() and i.hostname is None else i for i in bot.memory['nicks']]
    except:
        LOGGER.error(log.format('Error in whois catcher.'), exc_info=True)


def list_all_nicks(bot):
    '''Returns a flattened set of the current nicks that the bot can see in all channels.'''
    priv = dict(bot.privileges)
    return {n for c in priv.itervalues() for n in c}


@rule('.*')
@event('353')
@unblockable
@priority('high')
def names(bot, trigger):
    time.sleep(1)
    try:
        # Refresh list of nicks
        for id in list_all_nicks(bot):
            with bot.memory['nick_lock']:
                n = NickPlus(id, None)
                if n not in bot.memory['nicks']:  # If they're in it, they're already whois'd
                    whois(bot, n)
                    bot.memory['nicks'].append(n)
    except:
        LOGGER.error(log.format('Error in the names processing.'), exc_info=True)


@rule('.*')
@event('JOIN')
@unblockable
@thread(False)
@priority('high')
def join(bot, trigger):
    LOGGER.info(log.format('Caught JOIN by %s'), trigger.nick)
    try:
        if not trigger.sender.startswith('#'):
            # Only look at stuff from a channel
            return
        name = NickPlus(trigger.nick, trigger.host)
        with bot.memory['nick_lock']:
            # We don't want to check for name in list here, beacause of
            # erronious hostname matching
            bot.memory['nicks'].append(name)
    except:
        LOGGER.error(log.format('ERROR: bot nick list is unsynced from server'), exc_info=True)


@rule('.*')
@event('NICK')
@unblockable
@thread(False)
@priority('high')
def nick(bot, trigger):
    LOGGER.info(log.format('Caught NICK by %s >> %s'), trigger.nick, trigger)
    # Trigger doesn't come from channel. Any replies will be sent to user.
    # Old nick is in trigger.nick while new nick is in trigger and
    # trigger.sender
    try:
        old_nick = trigger.nick
        new_nick = NickPlus(trigger, trigger.host)
        with bot.memory['nick_lock']:
            bot.memory['nicks'].remove(old_nick)
            bot.memory['nicks'].append(new_nick)
    except:
        LOGGER.error(log.format('ERROR: bot nick list is unsynced from server'), exc_info=True)


@rule('.*')
@event('QUIT')
@unblockable
@thread(False)
@priority('high')
def quit(bot, trigger):
    LOGGER.info(log.format('Caught QUIT by %s (%s)'),  trigger.nick, trigger)
    # Quitting nick is trigger.nick, trigger and trigger.sender contain quit reason.
    try:
        name = trigger.nick  # Note that we're not using a NickPlus w/ hostname here
        with bot.memory['nick_lock']:
            if name in bot.memory['nicks']:
                LOGGER.info(log.format('Found %s in remove'), name)
                bot.memory['nicks'].remove(name)
            else:
                LOGGER.info(log.format('%s not found to remove'), name)
    except:
        LOGGER.error(log.format('ERROR: bot nick list is unsynced from server'), exc_info=True)


@rule('.*')
@event('KICK')
@unblockable
@thread(False)
@priority('high')
def kick(bot, trigger):
    # kicked = 4th part of bot.raw, kicker = trigger.nick, kick reason = trigger
    try:
        if not trigger.sender.startswith('#'):
            return
        if bot.raw:
            target = bot.raw.split()[3]
        else:
            target = trigger.raw.split()[3]
        LOGGER.info(log.format('Caught KICK of %s by %s in %s'), target, trigger.nick, trigger.sender)
        name = target
        with bot.memory['nick_lock']:
            if name == bot.nick:
                update_from_priv(bot)  # Bot got kicked, go through a full refresh
            else:
                bot.memory['nicks'].remove(name)
    except:
        LOGGER.error(log.format('ERROR: bot nick list is unsynced from server'), exc_info=True)


@rule('.*')
@event('PART')
@unblockable
@thread(False)
@priority('high')
def part(bot, trigger):
    LOGGER.info(log.format('Caught PART by %s from %s'), trigger.nick, trigger.sender)
    try:
        if not trigger.sender.startswith('#'):
            return
        name = trigger.nick  # Don't want to use a NickPlus because hostname matching
        with bot.memory['nick_lock']:
                if trigger.nick == bot.nick:
                    update_from_priv(bot)  # Bot left, go through a full refresh
                else:
                    bot.memory['nicks'].remove(name)
    except:
        LOGGER.error(log.format('ERROR: bot nick list is unsynced from server'), exc_info=True)


if __name__ == "__main__":
    print(__doc__.strip())
