"""
tod.py - A Willie module that manages a game of Truth or Dare
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function
from __future__ import unicode_literals

import bisect
import os.path
import random
import threading
import time

from willie.module import commands, interval

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
try:
    import nicks
except:
    import imp
    import sys
    try:
        print("trying manual import of nicks")
        fp, pathname, description = imp.find_module('nicks', [os.path.join('.', '.willie', 'modules')])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()
try:
    import colors
except:
    import imp
    import sys
    try:
        print("trying manual import of colors")
        fp, pathname, description = imp.find_module('colors', [os.path.join('.', '.willie', 'modules')])
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
    finally:
        if fp:
            fp.close()
try:
    import util
except:
    import imp
    import sys
    try:
        print("trying manual import of util")
        fp, pathname, description = imp.find_module('util', [os.path.join('.', '.willie', 'modules')])
        util = imp.load_source('util', pathname, fp)
        sys.modules['util'] = util
    finally:
        if fp:
            fp.close()


_EXPIRY = 90 * 60  # 90 minutes for list expiry
_MINIMUM = 5  # Minimum number of participants
_KICK_VOTES = 3


def configure(config):
    """
    | [truthordare] | example | purpose |
    | ---- | ------- | ------- |
    | channel | #channel | the channel where the truth or dare plugin will work |
    """
    if config.option('Limit the Truth or Dare plugin to a single channel', False):
        if not config.has_section('truthordare'):
            config.add_section('truthordare')
        config.add_list('truthordare',
                        'channel',
                        'Enter the channel to limit the T/D game to.',
                        'Channel:')


def setup(bot):
    if 'tod' not in bot.memory:
        bot.memory['tod'] = {}
    if 'list' not in bot.memory['tod']:
        bot.memory['tod']['list'] = []
    if 'inactive_list' not in bot.memory['tod']:
        bot.memory['tod']['inactive_list'] = []
    if 'lastactivity' not in bot.memory['tod']:
        bot.memory['tod']['lastactivity'] = None
    if 'lastspin' not in bot.memory['tod']:
        bot.memory['tod']['lastspin'] = None
    if 'lock' not in bot.memory:
        bot.memory['tod']['lock'] = threading.Lock()
    if 'clear_confirm' not in bot.memory['tod']:
        bot.memory['tod']['clear_confirm'] = False
    if 'vote_nick' not in bot.memory['tod']:
        bot.memory['tod']['vote_nick'] = ''
    if 'vote_count' not in bot.memory['tod']:
        bot.memory['tod']['vote_count'] = 0
    if 'channel' not in bot.memory['tod']:
        if bot.config.has_option('truthordare', 'channel'):
            bot.memory['tod']['channel'] = bot.config.truthordare.channel
        else:
            bot.memory['tod']['channel'] = None


def compile_nick_list(bot):  # to be used inside a with:lock statement
    return [i[0] for i in bot.memory['tod']['list']]


def weighted_choice(w):
    """Returns a random index from a list of tuples that contain
    (something, weight) where weight is the weighted probablity that
    that item should be chosen. Higher weights are chosen more often"""
    sum = 0
    sum_steps = []
    for item in w:
        sum = sum + int(item[1])
        sum_steps.append(sum)
    return bisect.bisect_right(sum_steps, random.uniform(0, sum))


def move_to_inactive(bot, participant):
    index = None
    for i in bot.memory['tod']['list']:
        bot.debug(__file__, log.format('comparing (%s, %s)' % i), 'verbose')
        if participant == i[0]:
            bot.debug(__file__, log.format('found (%s, %s)' % i), 'verbose')
            index = bot.memory['tod']['list'].index(i)
            bot.debug(__file__, log.format('index is %s' % index), 'verbose')
            break
    if index is not None:
        bot.memory['tod']['inactive_list'].append(bot.memory['tod']['list'].pop(index))
        return True
    else:
        return False


def move_to_list(bot, participant):
    index = None
    if not bot.memory['tod']['inactive_list']:
        return False
    for i in bot.memory['tod']['inactive_list']:
        bot.debug(__file__, log.format('comparing (%s, %s)' % i), 'verbose')
        if participant == i[0]:
            bot.debug(__file__, log.format('found (%s, %s)' % i), 'verbose')
            index = bot.memory['tod']['inactive_list'].index(i)
            bot.debug(__file__, log.format('index is %s' % index), 'verbose')
            break
    if index is not None:
        bot.memory['tod']['list'].append(bot.memory['tod']['inactive_list'].pop(index))
        return True
    else:
        return False


@commands('tod_join')
def join(bot, trigger):
    """This command is used to add yourself to a Truth or Dare session."""
    # Don't allow PMs
    if not trigger.sender.startswith('#'):
        return
    # Prevent certain nicks
    if util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    # return if we're not in the configured channel, if configured.
    if bot.memory['tod']['channel'] and trigger.sender != bot.memory['tod']['channel']:
        return
    with bot.memory['tod']['lock']:
        bot.memory['tod']['lastactivity'] = time.time()
        participant = nicks.NickPlus(trigger.nick, trigger.host)
        bot.debug(__file__, log.format('TOD join for %s, %s' % (trigger.nick, trigger.host)), 'verbose')

        if move_to_list(bot, participant):
            bot.reply("You are back in the truth or dare list.")
        else:
            if participant not in compile_nick_list(bot):
                if len(compile_nick_list(bot)) < 2:
                    bot.memory['tod']['list'].append((participant, 1))
                else:
                    bot.memory['tod']['list'].append((participant, len(compile_nick_list(bot)) / 2))
                bot.reply("You are now in the truth or dare list.")
            else:
                bot.reply("You are already in the truth or dare list!")


@commands('tod_leave', 'tod_quit', 'tod_bail')
def leave(bot, trigger):
    """This command is used to remove yourself to a Truth or Dare session. """
    # Don't allow PMs
    if not trigger.sender.startswith('#'):
        return
    # Prevent certain nicks
    if util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    # return if we're not in the configured channel, if configured.
    if bot.memory['tod']['channel'] and trigger.sender != bot.memory['tod']['channel']:
        return
    with bot.memory['tod']['lock']:
        bot.memory['tod']['lastactivity'] = time.time()
        participant = nicks.NickPlus(trigger.nick, trigger.host)
        bot.debug(__file__, log.format('TOD quit for %s' % participant), 'verbose')
        if move_to_inactive(bot, participant):
            bot.reply("You are no longer in the truth or dare list")
        else:
            bot.reply("You weren't in the truth or dare list!")


@commands('spin', 'tod_next', 'tod_spin')
def spin(bot, trigger):
    """This command is used to choose the next target for a Truth or Dare session. """
    def pick_nick(bot):
        next_nick = ' '
        bot.debug(__file__, log.format('next_nick is "%s"' % next_nick), 'verbose')
        bot.debug(__file__, log.format('in_chan returns %s' % nicks.in_chan(bot, trigger.sender, next_nick)), 'verbose')

        while not nicks.in_chan(bot, trigger.sender, next_nick):  # pick people until we get someone in the room.
            next = weighted_choice(bot.memory['tod']['list'])
            next_nick = bot.memory['tod']['list'][next][0]
            bot.debug(__file__, log.format('next_nick is "%s"' % next_nick), 'verbose')

        # Check to see if their nick is different and use that
        nick_list = []
        nick_list.extend(nicks.in_chan(bot, trigger.sender))
        nick_list = [i for i in nick_list if not util.ignore_nick(bot, i)]

        n = nick_list.index(next_nick)
        next_nick = nick_list.pop(n)  # This is the current and perhaps updated nickname

        # remove the choice from the list and set weight to -2 to prevent
        # it from being picked on the next two round.
        choice = bot.memory['tod']['list'].pop(next)  # This is the original and perhaps old nickname tuple
        choice = (next_nick, -2)
        bot.memory['tod']['list'].append(choice)

        # Increment all weights
        bot.memory['tod']['list'] = [(i[0], i[1] + 1) for i in bot.memory['tod']['list']]
        return choice[0]

    # Don't allow PMs
    if not trigger.sender.startswith('#'):
        return
    # Prevent certain nicks
    if util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    # return if we're not in the configured channel, if configured.
    if bot.memory['tod']['channel'] and trigger.sender != bot.memory['tod']['channel']:
        return
    with bot.memory['tod']['lock']:
        nick_list = []
        nick_list.extend(nicks.in_chan(bot, trigger.sender))
        nick_list = [i for i in nick_list if not util.ignore_nick(bot, i)]

        if bot.memory['tod']['lastspin'] > time.time() - 15:
            return
        elif len([i[0] for i in bot.memory['tod']['list'] if i[0] in nick_list]) < _MINIMUM:
            bot.say("Sorry, but we don't have enough participants! We need at least %i people to join." % _MINIMUM)
        else:
            if bot.memory['tod']['lastspin'] is None:  # pick two nicks if we haven't started a session
                choice1 = pick_nick(bot)
                choice2 = pick_nick(bot)
                bot.say(
                    colors.colorize(
                        random.choice([
                            'We\'ll have %s start by asking %s ',
                            'Okay, %s asks %s ',
                            'To start, %s will ask %s ']) % (choice1, choice2),
                        ['magenta'], ['bold']))
            else:  # Pick one if we are in the middle of a session
                choice = pick_nick(bot)
                bot.say(
                    colors.colorize(
                        random.choice([
                            'Next up, %s ',
                            'Okay %s, Truth or Dare?',
                            'Your turn, %s ',
                            'Time to choose, %s',
                            'You\'re up, %s ']) % choice,
                        ['magenta'], ['bold']))
            bot.memory['tod']['lastactivity'] = time.time()
            bot.memory['tod']['lastspin'] = time.time()


@commands('tod_list', 'tod_who')
def list(bot, trigger):
    """This command is used to list those participating in Truth or Dare. """
    # Don't allow PMs
    if not trigger.sender.startswith('#'):
        return
    # Prevent certain nicks
    if util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    # return if we're not in the configured channel, if configured.
    if bot.memory['tod']['channel'] and trigger.sender != bot.memory['tod']['channel']:
        return
    with bot.memory['tod']['lock']:
        participants = compile_nick_list(bot)
        message = 'The current participants include:'
        # Parse through channel nicks to get updated nicks
        nick_list = []
        nick_list.extend(nicks.in_chan(bot, trigger.sender))
        # First filter excludes
        nick_list = [i for i in nick_list if not util.ignore_nick(bot, i)]

        for participant in participants:
            if nicks.in_chan(bot, trigger.sender, participant):
                try:
                    i = nick_list.index(participant)
                    participant = nick_list.pop(i)
                    message = '%s %s,' % (message, participant)
                except ValueError:
                    pass  # multiple nicks can beak things
        message = message.strip(',')
        if message == 'The current participants include:':
            bot.say("No one is participating right now.")
        else:
            bot.say(message)


@commands('truthordare', 'tod', 'tord')
def tod(bot, trigger):
    """To join, use !tod_join. To leave, use !tod_leave. To pick the next person, use !spin."""
    bot.say(tod.__doc__.strip())


@commands('tod_clear', 'tod_end')
def clear(bot, trigger):
    """Clears the list of participants for a Truth or Dare session."""
    # Don't allow PMs
    if not trigger.sender.startswith('#'):
        return
    # Prevent certain nicks
    if util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    # return if we're not in the configured channel, if configured.
    if bot.memory['tod']['channel'] and trigger.sender != bot.memory['tod']['channel']:
        return
    if bot.memory['tod']['clear_confirm']:
        with bot.memory['tod']['lock']:
            bot.memory['tod']['list'] = []
            bot.memory['tod']['inactive_list'] = []
            bot.memory['tod']['lastactivity'] = None
            bot.memory['tod']['lastspin'] = None
            bot.reply('The truth or dare list has been cleared')
            bot.memory['tod']['clear_confirm'] = False
            bot.memory['tod']['vote_nick'] = ''
            bot.memory['tod']['vote_count'] = 0
    else:
        bot.reply('Are you sure you want to clear the truth or dare list? Use this command again within 20s to confirm.')
        bot.memory['tod']['clear_confirm'] = True
        time.sleep(20)
        bot.memory['tod']['clear_confirm'] = False


@interval(1000)
def clear_when_dead(bot):
    bot.debug(__file__, log.format('Checking TOD list for inactivity.'), 'verbose')
    bot.debug(__file__, log.format('last activity was %s' % bot.memory['tod']['lastactivity']), 'verbose')
    bot.debug(__file__, log.format('now is %s' % time.time()), 'verbose')
    if bot.memory['tod']['list'] and bot.memory['tod']['lastactivity'] and bot.memory['tod']['lastactivity'] < time.time() - _EXPIRY:
        bot.debug(__file__, log.format('Clearing TOD list due to inactivity'), 'verbose')
        bot.memory['tod']['list'] = []
        bot.memory['tod']['inactive_list'] = []
        bot.memory['tod']['lastactivity'] = None
        bot.memory['tod']['lastspin'] = None
        bot.memory['tod']['vote_nick'] = ''
        bot.memory['tod']['vote_count'] = 0


@commands('tod_choose_for_me', 'tod_random', 'tod_choose')
def template(bot, trigger):
    """Chooses "Truth" or "Dare" for you randomly."""
    # Don't allow PMs
    if not trigger.sender.startswith('#'):
        return
    # Prevent certain nicks
    if util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    # return if we're not in the configured channel, if configured.
    if bot.memory['tod']['channel'] and trigger.sender != bot.memory['tod']['channel']:
        return
    bot.reply(random.choice(['Truth', 'Dare']))


@commands('tod_vote', 'tod_kick')
def kick(bot, trigger):
    """Used to vote idle people out of a Truth or Dare session."""
    # Don't allow PMs
    if not trigger.sender.startswith('#'):
        return
    # Prevent certain nicks
    if util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    # return if we're not in the configured channel, if configured.
    if bot.memory['tod']['channel'] and trigger.sender != bot.memory['tod']['channel']:
        return
    try:
        target = nicks.NickPlus(trigger.args[1].split()[1])
    except IndexError:
        return
    participant = nicks.NickPlus(trigger.nick, trigger.host)
    with bot.memory['tod']['lock']:
        if participant not in compile_nick_list(bot):
            bot.say("You can't vote if you're not playing!")
            return
    if bot.memory['tod']['vote_nick']:
        with bot.memory['tod']['lock']:
            if target == bot.memory['tod']['vote_nick']:
                if bot.memory['tod']['vote_count'] == _KICK_VOTES - 1:
                    bot.say('%s kicked from Truth or dare. Use !tod_join to rejoin.' % target)
                    move_to_inactive(bot, target)
                    bot.memory['tod']['vote_nick'] = ''
                    bot.memory['tod']['vote_count'] = 0
                else:
                    bot.memory['tod']['vote_count'] += 1
                    bot.reply('%i votes of %i needed to kick.' % (bot.memory['tod']['vote_count'], _KICK_VOTES))
            else:
                bot.reply("Sorry, currently voting on %s" % bot.memory['tod']['vote_nick'])
    else:
        with bot.memory['tod']['lock']:
            if target in compile_nick_list(bot):
                bot.memory['tod']['vote_nick'] = target
                bot.memory['tod']['vote_count'] += 1
                bot.say('Kick vote started for %s. %i more votes in the next 60 seconds are required.' % (target, _KICK_VOTES - 1))
            else:
                bot.reply("Sorry, I didn't find that.")
        time.sleep(60)
        with bot.memory['tod']['lock']:
            if bot.memory['tod']['vote_count'] < _KICK_VOTES and bot.memory['tod']['vote_count'] != 0:
                bot.say("Vote failed.")
            bot.memory['tod']['vote_nick'] = ''
            bot.memory['tod']['vote_count'] = 0


if __name__ == "__main__":
    print(__doc__.strip())
