"""
ping.py - A simple ping module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from willie.module import commands, priority, example


@commands(u'ping')
@priority(u'high')
@example(u'!ping')
def ping(bot, trigger):
    bot.say(u'Pony!')


if __name__ == "__main__":
    print __doc__.strip()
