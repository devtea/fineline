"""
choose.py - A simple Willie module that chooses randomly between arguments
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import random

from willie.module import commands, example

random.seed()


@commands(u'choose')
@example(ur"!choose 2, The Hobbit, Ender's Game, The Golden Compass")
def choose(Willie, trigger):
    """Returns a random selection of comma separated items provided to it.
    Chooses a subset if the first argument is an integer."""

    Willie.debug(u"choose.py", u"==============", u"verbose")
    Willie.debug(u"choose.py", u"Module called.", u"verbose")
    # Parse the provided arguments into a list of strings
    Willie.debug(u"choose.py trigger.args", trigger.args, u"verbose")
    __, __, list = trigger.args[1].partition(u' ')
    # Test for csv or space separated values
    if u',' in trigger.args[1]:
        Willie.debug(u"choose.py list", list, u"verbose")
        args = list.split(u',')
        Willie.debug(u"choose.py args", args, u"verbose")
    else:
        args = list.split()
    # Strip the strings
    for i, str in enumerate(args):
        args[i] = str.strip()
    Willie.debug(u"choose.py", args, u"verbose")
    if len(args) > 1:
        # If the first argument is an int, we'll want to use it
        if args[0].isdigit():
            Willie.debug(u"choose.py", u"First arg is a number.", u"verbose")
            # Cast the string to an int so it's usable
            choices = int(float(args.pop(0)))
            # Test for sanity
            if choices < len(args) and choices > 0:
                Willie.debug(u"choose.py",
                             u"Choice number is sane.",
                             u"verbose"
                             )
                # run through choices and add the selections to a list
                choice_list = []
                for i in range(choices):
                    last_choice = random.choice(args)
                    args.remove(last_choice)
                    Willie.debug(u"choose.py",
                                 u"Adding Choice " + last_choice,
                                 u"verbose")
                    choice_list.append(last_choice)
                Willie.reply(u', '.join(choice_list))
            else:
                # The number is too small or too large to be useful
                Willie.debug(u"choose.py",
                             u"Choice number is not sane.",
                             u"verbose")
                Willie.reply(u"Hmm, how about everything?")
        else:
            # Just choose one item since no number was specified
            Willie.debug(u"choose.py",
                         u"First arg is not a number.",
                         u"verbose"
                         )
            choice = random.choice(args)
            Willie.reply(choice)
    else:
        # <=1 items is not enough to choose from!
        Willie.debug(u"choose.py", u"Not enough args.", u"verbose")
        Willie.reply(u"You didn't give me enough to choose from!")


if __name__ == "__main__":
    print __doc__.strip()
