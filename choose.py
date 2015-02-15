# coding=utf8
"""
choose.py - A simple willie module that chooses randomly between arguments
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import bisect
import random
import time

from willie.logger import get_logger
from willie.module import commands, example

LOGGER = get_logger(__name__)

random.seed()

TIME_LIMIT = 500

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

try:
    import nicks
except:
    import imp
    import sys
    import os.path
    try:
        LOGGER.info(log.format("trying manual import of nicks"))
        fp, pathname, description = imp.find_module('nicks', [os.path.join('.', '.willie', 'modules')])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()


def setup(bot):
    bot.memory['choose'] = {}


def allocate(bot, nick, returns, choices):
    LOGGER.info(log.format('Allocating %s for %s from %s.'), returns, nick, choices)
    if returns == 1:
        if nick not in bot.memory['choose'] or time.time() - bot.memory['choose'][nick] > TIME_LIMIT:
            LOGGER.info(log.format('Nick not in list or plenty of time has passed.'))
            choice = weighted_choice(bot, choices)
        else:
            LOGGER.info(log.format('Nick has choosen recently'))
            choice = unweighted_choice(choices, returns)
    else:
        LOGGER.info(log.format('Defaulting to unweighted choice.'))
        choice = unweighted_choice(choices, returns)
    return choice


def weighted_choice(bot, unweighted):
    def choose(w):
        """Returns a random index from a list of tuples that contain
        (something, weight) where weight is the weighted probablity that
        that item should be chosen. Higher weights are chosen more often"""
        sum = 0
        sum_steps = []
        for item in w:
            sum = sum + int(item[1])
            sum_steps.append(sum)
        return bisect.bisect_right(sum_steps, random.uniform(0, sum))

    good = ['art', 'arting', 'artistic', 'arty', 'create', 'creative', 'draw',
            'drawing', 'paint', 'painting', 'sketch', 'sketching', 'study',
            'studies', 'studying', 'aeyrt', 'tar', 'tea', 'cook', 'productive',
            'fzoo', 'fzooo', 'fzoooo', 'fzooooo', 'fzoooooo', 'fzooooooo', 'piirrä']
    bad = ['don\'t', 'dont', 'fuck', 'later', 'no', 'not', 'never', 'quit',
           'lame', 'stupid', 'dumb', 'bad', 'out', 'sucks', 'sucky', 'worse',
           'hitler', 'fcuk', 'fook', 'fock', 'stop', 'but', 'dum', 'freak',
           'freaks', 'freaky', 'silly', 'älä']

    LOGGER.info(log.format('Weighting choices from %s.'), unweighted)
    weighted = []
    while unweighted:
        i = unweighted.pop()
        LOGGER.info(log.format('Processing choice "%s"".'), i)
        if set(i.split()).intersection(good):
            if set(i.split()).intersection(bad):
                LOGGER.info(log.format('  Found choice in bad list.'))
                weighted.append((i, 1))
            else:
                LOGGER.info(log.format('  Found choice in good list.'))
                weighted.append((i, 525))
        else:
            LOGGER.info(log.format('  Normal choice.'))
            weighted.append((i, 75))
    LOGGER.info(log.format('Weighted list is %s.'), weighted)

    i = choose(weighted)
    LOGGER.info(log.format('got index %s'), i)
    LOGGER.info(log.format('Returning "%s"'), weighted[i][0])
    return [weighted[i][0]]


def unweighted_choice(unweighted, choices):
    if choices < len(unweighted) and choices > 0:
        # run through choices and add the selections to a list
        choice_list = []
        for i in range(choices):
            last_choice = random.choice(unweighted)
            unweighted.remove(last_choice)
            choice_list.append(last_choice)
        return choice_list
    else:
        # The number is too small or too large to be useful
        return None


@commands('choose', 'pick', 'select')
@example(ur"!choose 2, The Hobbit, Ender's Game, The Golden Compass")
def choose(bot, trigger):
    """Returns a selection of comma separated items provided to it.
    If the first option is an integer, it will choose that many items if possible"""

    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    now = time.time()

    # Parse the provided arguments into a list of strings
    LOGGER.info(log.format("Trigger args: ", trigger.args))
    __, __, list = trigger.args[1].partition(' ')
    # Test for csv or space separated values
    if ',' in trigger.args[1]:
        LOGGER.info(log.format('list: ', list))
        args = list.split(',')
        LOGGER.info(log.format('args: ', args))
    else:
        args = list.split()
    # Strip the strings
    for i, str in enumerate(args):
        args[i] = str.strip()
    LOGGER.info(log.format('args: ', args))
    if len(args) > 1:
        caller = nicks.Identifier(trigger.nick)
        # If the first argument is an int, we'll want to use it
        if args[0].isdigit():
            LOGGER.info(log.format("First arg is a number."))
            # Cast the string to an int so it's usable
            choices = int(float(args.pop(0)))

            choice = allocate(bot, caller, choices, args)

            if choice:
                if len(choice) > 1:
                    bot.reply(', '.join(choice))
                else:
                    bot.reply(choice[0])
            else:
                bot.reply("Hmm, how about everything?")

        else:
            # Just choose one item since no number was specified
            LOGGER.info(log.format("First arg is not a number."))
            # choice = random.choice(args)
            choice = allocate(bot, caller, 1, args)
            if choice:
                bot.reply(choice[0])
            else:
                bot.reply("Hmm, how about everything?")
    else:
        # <=1 items is not enough to choose from!
        bot.reply("You didn't give me enough to choose from!")

    bot.memory['choose'][nicks.Identifier(trigger.nick)] = now
    LOGGER.info(log.format("Updated last choose time for nick."))
    LOGGER.info(log.format("=" * 20))


if __name__ == "__main__":
    print(__doc__.strip())
