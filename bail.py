"""
bail.py - A Willie module that does something
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

from willie.module import commands


@commands('bail')
def bail(bot, trigger):
    bot.say(u'Uh oh! Looks like %s is bailing out. Good luck!' % trigger.nick)


if __name__ == "__main__":
    print(__doc__.strip())
