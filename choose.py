"""
choose.py - A simple Willie module that chooses randomly between arguments
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import random

def choose(Willie, trigger):
    """Returns a random selection of items provided to it."""

    args = trigger.args.pop().split()
    args.pop(0)
    choice = random.choice(args)
    Willie.reply(choice)

choose.commands = ['choose']

#Priorities of 'high', 'medium', and 'low' work
choose.priority = 'medium'

#Limit in seconds of users ability to trigger module
choose.rate = 15

#Example used in help query to bot for commands
choose.example = "!choose apple orange pear"

if __name__ == "__main__":
    print __doc__.strip()
