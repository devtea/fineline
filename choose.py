"""
choose.py - A simple willie module that chooses randomly between arguments
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import bisect
import os.path
import random
import time

from willie.module import commands, example

random.seed()

TIME_LIMIT = 500

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


def setup(bot):
    bot.memory['choose'] = {}


def allocate(bot, nick, returns, choices):
    bot.debug(__file__, log.format(u'Allocating %s for %s from %s.' % (returns, nick, choices)), 'verbose')
    if returns == 1:
        if nick not in bot.memory['choose'] or time.time() - bot.memory['choose'][nick] > TIME_LIMIT:
            bot.debug(__file__, log.format(u'Nick not in list or plenty of time has passed.'), 'verbose')
            choice = weighted_choice(bot, choices)
        else:
            bot.debug(__file__, log.format(u'Nick has choosen recently'), 'verbose')
            choice = unweighted_choice(choices, returns)
    else:
        bot.debug(__file__, log.format(u'Defaulting to unweighted choice.'), 'verbose')
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
            'studies', 'studying', 'aeyrt', 'tar', 'tea', 'cook', 'productive']
    bad = ['don\'t', 'dont', 'fuck', 'later', 'no', 'not', 'never', 'quit',
           'lame', 'stupid', 'dumb', 'bad', 'out', 'sucks', 'sucky', 'worse',
           'hitler', 'fcuk', 'fook', 'fock', 'stop', 'but', 'dum', 'freak',
           'freaks', 'freaky']

    bot.debug(__file__, log.format(u'Weighting choices from %s.' % unweighted), 'verbose')
    weighted = []
    while unweighted:
        i = unweighted.pop()
        bot.debug(__file__, log.format(u'Processing choice "%s"".' % i), 'verbose')
        if set(i.split()).intersection(good):
            if set(i.split()).intersection(bad):
                bot.debug(__file__, log.format(u'  Found choice in bad list.'), 'verbose')
                weighted.append((i, 1))
            else:
                bot.debug(__file__, log.format(u'  Found choice in good list.'), 'verbose')
                weighted.append((i, 10000))
        else:
            bot.debug(__file__, log.format(u'  Normal choice.'), 'verbose')
            weighted.append((i, 150))
    bot.debug(__file__, log.format(u'Weighted list is %s.' % weighted), 'verbose')

    i = choose(weighted)
    bot.debug(__file__, log.format(u'got index %s' % i), 'verbose')
    bot.debug(__file__, log.format(u'Returning "%s"' % weighted[i][0]), 'verbose')
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


@commands(u'choose', 'pick', 'select')
@example(ur"!choose 2, The Hobbit, Ender's Game, The Golden Compass")
def choose(bot, trigger):
    """Returns a random selection of comma separated items provided to it.
    Chooses a subset if the first argument is an integer."""

    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    now = time.time()

    # Parse the provided arguments into a list of strings
    bot.debug(__file__, log.format("Trigger args: ", trigger.args), u"verbose")
    __, __, list = trigger.args[1].partition(u' ')
    # Test for csv or space separated values
    if u',' in trigger.args[1]:
        bot.debug(__file__, log.format('list: ', list), u"verbose")
        args = list.split(u',')
        bot.debug(__file__, log.format('args: ', args), u"verbose")
    else:
        args = list.split()
    # Strip the strings
    for i, str in enumerate(args):
        args[i] = str.strip()
    bot.debug(__file__, log.format('args: ', args), u"verbose")
    if len(args) > 1:
        caller = nicks.Nick(trigger.nick)
        # If the first argument is an int, we'll want to use it
        if args[0].isdigit():
            bot.debug(__file__, log.format(u"First arg is a number."), u"verbose")
            # Cast the string to an int so it's usable
            choices = int(float(args.pop(0)))

            choice = allocate(bot, caller, choices, args)

            if choice:
                if len(choice) > 1:
                    bot.reply(u', '.join(choice))
                else:
                    bot.reply(choice[0])
            else:
                bot.reply(u"Hmm, how about everything?")

        else:
            # Just choose one item since no number was specified
            bot.debug(__file__, log.format(u"First arg is not a number."), u"verbose")
            # choice = random.choice(args)
            choice = allocate(bot, caller, 1, args)
            if choice:
                bot.reply(choice[0])
            else:
                bot.reply(u"Hmm, how about everything?")
    else:
        # <=1 items is not enough to choose from!
        bot.debug(__file__, log.format(u"Not enough args."), u"verbose")
        bot.reply(u"You didn't give me enough to choose from!")

    bot.memory['choose'][nicks.Nick(trigger.nick)] = now
    bot.debug(__file__, log.format(u"Updated last choose time for nick."), u"verbose")
    bot.debug(__file__, log.format(u"=" * 20), u"verbose")


if __name__ == "__main__":
    print(__doc__.strip())
