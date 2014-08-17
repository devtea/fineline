"""
tod.py - A Willie module that manages a game of Truth or Dare
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function
from __future__ import unicode_literals

import bisect
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
        fp, pathname, description = imp.find_module('log', ['./.willie/modules/'])
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
        fp, pathname, description = imp.find_module('nicks', ['./.willie/modules/'])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()

_EXPIRY = 90 * 60  # 90 minutes for list expiry
_MINIMUM = 5  # Minimum number of participants
_excludes = ['fineline', 'feignline', 'hushmachine', 'finelinefan', 'hushrobot', 'oppobot']

def setup(bot):
    if 'tod' not in bot.memory:
        bot.memory['tod'] = {}
    if 'list' not in bot.memory['tod']:
        bot.memory['tod']['list'] = []
    if 'last' not in bot.memory['tod']:
        bot.memory['tod']['last'] = None
    if 'lock' not in bot.memory:
        bot.memory['tod']['lock'] = threading.Lock()
    if 'confirm' not in bot.memory['tod']:
        bot.memory['tod']['confirm'] = False


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


@commands('tod_join')
def join(bot, trigger):
    """This command is used to add yourself to a Truth or Dare session. """
    if not trigger.sender.startswith('#') or trigger.nick in _excludes:
        return
    with bot.memory['tod']['lock']:
        participant = nicks.NickPlus(trigger.nick, trigger.host)
        bot.debug(__file__, log.format('TOD join for %s, %s' % (trigger.nick, trigger.host)), 'verbose')

        if participant not in compile_nick_list(bot):
            if len(compile_nick_list(bot)) < 2:
                bot.memory['tod']['list'].append((participant, 1))
            else:
                bot.memory['tod']['list'].append((participant, len(compile_nick_list(bot)) / 2))
            bot.reply("You now in the truth or dare list.")
        else:
            bot.reply("You are already in the truth or dare list!")


@commands('tod_leave', 'tod_quit', 'tod_bail')
def leave(bot, trigger):
    """This command is used to remove yourself to a Truth or Dare session. """
    if not trigger.sender.startswith('#') or trigger.nick in _excludes:
        return
    with bot.memory['tod']['lock']:
        participant = nicks.NickPlus(trigger.nick, trigger.host)
        bot.debug(__file__, log.format('TOD quit for %s' % participant), 'verbose')

        index = None
        for i in bot.memory['tod']['list']:
            bot.debug(__file__, log.format('comparing (%s, %s)' % i), 'verbose')
            if participant == i[0]:
                bot.debug(__file__, log.format('found (%s, %s)' % i), 'verbose')
                index = bot.memory['tod']['list'].index(i)
                bot.debug(__file__, log.format('index is %s' % index), 'verbose')
                break
        if index is not None:
            bot.memory['tod']['list'].pop(index)
            bot.reply("You no longer in the truth or dare list")
        else:
            bot.reply("You weren't in the truth or dare list!")


@commands('spin', 'tod_next', 'tod_spin')
def spin(bot, trigger):
    """This command is used to choose the next target for a Truth or Dare session. """
    if not trigger.sender.startswith('#') or trigger.nick in _excludes:
        return
    with bot.memory['tod']['lock']:
        nick_list = []
        nick_list.extend(nicks.in_chan(bot, trigger.sender))
        nick_list = [i for i in nick_list if i not in _excludes]

        if len([i[0] for i in bot.memory['tod']['list'] if i[0] in nick_list]) < _MINIMUM:
            bot.say("Sorry, but we don't have enough participants yet! We need at least %i people to join." % _MINIMUM)
        else:
            bot.memory['tod']['last'] = time.time()

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
            nick_list = [i for i in nick_list if i not in _excludes]

            n = nick_list.index(next_nick)
            next_nick = nick_list.pop(n)  # This is the current and perhaps updated nickname

            # remove the choice from the list and set weight to -2 to prevent
            # it from being picked on the next two round.
            choice = bot.memory['tod']['list'].pop(next)  # This is the original and perhaps old nickname tuple
            choice = (next_nick, -2)
            bot.memory['tod']['list'].append(choice)

            # Increment all weights
            bot.memory['tod']['list'] = [(i[0], i[1] + 1) for i in bot.memory['tod']['list']]

            # announce choice
            # TODO variety
            bot.say(random.choice([
                '%s is next!' % choice[0],
                '%s: Truth or dare?' % choice[0],
                'Your turn, %s!' % choice[0],
                'Time to choose, %s. Truth or dare?' % choice[0],
                "%s, you're up!" % choice[0]]))


@commands('tod_list', 'tod_who')
def list(bot, trigger):
    """This command is used to list those participating in Truth or Dare. """
    if not trigger.sender.startswith('#') or trigger.nick in _excludes:
        return
    with bot.memory['tod']['lock']:
        participants = compile_nick_list(bot)
        message = 'The current participants include:'
        # Parse through channel nicks to get updated nicks
        nick_list = []
        nick_list.extend(nicks.in_chan(bot, trigger.sender))
        # First filter excludes
        nick_list = [i for i in nick_list if i not in _excludes]

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


@commands('tod', 'truthordare', 'tord')
def tod(bot, trigger):
    """To start a truth or dare session, have at least five people join. To join, use
 !tod_join. To leave, use !tod_leave. To pick the next person, use !spin."""
    bot.say(tod.__doc__.strip())


@commands('tod_clear', 'tod_end')
def clear(bot, trigger):
    """Clears the list of participants for a Truth or Dare session."""
    if not trigger.sender.startswith('#') or trigger.nick in _excludes:
        return
    if bot.memory['tod']['confirm']:
        with bot.memory['tod']['lock']:
            bot.memory['tod']['list'] = []
            bot.reply('The truth or dare list has been cleared')
            bot.memory['tod']['confirm'] = False
    else:
        bot.reply('Are you sure you want to clear the truth or dare list? Use this command again within 20s to confirm.')
        bot.memory['tod']['confirm'] = True
        time.sleep(20)
        bot.memory['tod']['confirm'] = False


@interval(1000)
def clear_when_dead(bot, trigger):
    if bot.memory['tod']['list'] and bot.memory['tod']['last'] and bot.memory['tod']['last'] < time.time() - _EXPIRY:
        bot.debug(__file__, log.format('Clearing TOD list due to inactivity'), 'verbose')
        bot.memory['tod']['list'] = []


@commands('tod_choose_for_me', 'tod_random', 'tod_choose')
def template(bot, trigger):
    """Chooses "Truth" or "Dare" randomly."""
    if not trigger.sender.startswith('#') or trigger.nick in _excludes:
        return
    bot.reply(random.choice(['Truth', 'Dare']))


if __name__ == "__main__":
    print(__doc__.strip())
