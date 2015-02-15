"""
about.py - A simple Willie information module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import time

from willie.module import commands

random.seed()


@commands('about')
def about(bot, trigger):
    """Shares basic information on the bot."""
    time.sleep(random.uniform(2, 4))
    bot.say(u"Hello, my name is %s and I'm a bot! " % bot.nick)


@commands('bugs', 'bug')
def bugs(bot, trigger):
    """Shares bug reporting information for the bot."""
    if len(trigger.strip()) > 5:
        return
    time.sleep(random.uniform(2, 4))
    bot.say('Bugs?! I don\'t have any bugs!')
    time.sleep(random.uniform(2, 4))
    bot.say(u"But I guess if you think you've found one, you can " +
            "make a bug report at " +
            "https://bitbucket.org/tdreyer/fineline/issues")


@commands('source')
def source(bot, trigger):
    """Links to the bot's source code"""
    time.sleep(random.uniform(2, 4))
    bot.say("You can see my source at http://willie.dftba.net/ and " +
            "my plugins at http://bitbucket.org/tdreyer/fineline")


if __name__ == "__main__":
    print __doc__.strip()
