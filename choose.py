"""
choose.py - A simple willie module that chooses randomly between arguments
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import random

from willie.module import commands, example

random.seed()

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


@commands(u'choose')
@example(ur"!choose 2, The Hobbit, Ender's Game, The Golden Compass")
def choose(bot, trigger):
    """Returns a random selection of comma separated items provided to it.
    Chooses a subset if the first argument is an integer."""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    bot.debug(__file__, log.format(u"=============="), u"verbose")
    bot.debug(__file__, log.format(u"Module called."), u"verbose")
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
        # If the first argument is an int, we'll want to use it
        if args[0].isdigit():
            bot.debug(__file__, log.format(u"First arg is a number."), u"verbose")
            # Cast the string to an int so it's usable
            choices = int(float(args.pop(0)))
            # Test for sanity
            if choices < len(args) and choices > 0:
                bot.debug(__file__, log.format(u"Choice number is sane."), u"verbose")
                # run through choices and add the selections to a list
                choice_list = []
                for i in range(choices):
                    last_choice = random.choice(args)
                    args.remove(last_choice)
                    bot.debug(__file__, log.format(u"Adding Choice ", last_choice), u"verbose")
                    choice_list.append(last_choice)
                bot.reply(u', '.join(choice_list))
            else:
                # The number is too small or too large to be useful
                bot.debug(__file__, log.format(u"Choice number is not sane."), u"verbose")
                bot.reply(u"Hmm, how about everything?")
        else:
            # Just choose one item since no number was specified
            bot.debug(__file__, log.format(u"First arg is not a number."), u"verbose")
            choice = random.choice(args)
            bot.reply(choice)
    else:
        # <=1 items is not enough to choose from!
        bot.debug(__file__, log.format(u"Not enough args."), u"verbose")
        bot.reply(u"You didn't give me enough to choose from!")


if __name__ == "__main__":
    print(__doc__.strip())
