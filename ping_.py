"""
ping.py - A simple ping module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from willie.module import commands, priority, example


@commands('ping')
@priority('high')
@example('!ping')
def ping(bot, trigger):
    bot.say('Pony!')


if __name__ == "__main__":
    print(__doc__.strip())
