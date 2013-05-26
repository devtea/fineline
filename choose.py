"""
choose.py - A simple Willie module that chooses randomly between arguments
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import random

random.seed()

def choose(Willie, trigger):
    """Returns a random selection of items provided to it.
    Chooses a subset if the first argument is an integer."""

    Willie.debug("choose.py", "==============", "verbose")
    Willie.debug("choose.py", "Module called.", "verbose")

    # Parse the provided arguments into a list of strings
    Willie.debug("choose.py trigger.args",trigger.args, "verbose")
    __, __, list = trigger.args[1].partition(' ')
    # Test for csv or space separated values
    if ',' in trigger.args[1]:
        Willie.debug("choose.py list", list, "verbose")
        args = list.split(',')
        Willie.debug("choose.py args", args, "verbose")
    else:
        args = list.split()

    # Strip the strings
    for i, str in enumerate(args):
        args[i] = str.strip()

    Willie.debug("choose.py", args, "verbose")

    if len(args) > 1:
        # If the first argument is an int, we'll want to use it
        if args[0].isdigit():
            Willie.debug("choose.py", "First arg is a number.", "verbose")

            # Cast the string to an int so it's usable
            choices = int(float(args.pop(0)))
            # Test for sanity
            if choices < len(args) and choices > 0:
                Willie.debug("choose.py", "Choice number is sane.", "verbose")

                # run through choices and add the selections to a list
                choice_list = []
                for i in range(choices):
                    last_choice = random.choice(args)
                    args.remove(last_choice)
                    Willie.debug("choose.py", "Adding Choice " + last_choice,
                            "verbose")
                    choice_list.append(last_choice)
                Willie.reply(', '.join(choice_list))
            else:
                # The number is too small or too large to be useful
                Willie.debug("choose.py", "Choice number is not sane.",
                        "verbose")
                Willie.reply("Hmm, how about everything?")
        else:
            # Just choose one item since no number was specified
            Willie.debug("choose.py", "First arg is not a number.", "verbose")
            choice = random.choice(args)
            Willie.reply(choice)
    else:
        # <=1 items is not enough to choose from!
        Willie.debug("choose.py", "Not enough args.", "verbose")
        Willie.reply("You didn't give me enough to choose from!")
# Match a command sequence eg !cmd
choose.commands = ['choose']

# Priorities of 'high', 'medium', and 'low' work
choose.priority = 'medium'

# Limit in seconds of users ability to trigger module
choose.rate = 15

# Example used in help query to bot for commands
choose.example = '"!choose apple orange pear" or ' + \
        '"!choose 2 red blue green orange" or ' + \
        '"!choose 2, The Hobbit, Ender\'s Game, The Golden Compass"'



if __name__ == "__main__":
    print __doc__.strip()
