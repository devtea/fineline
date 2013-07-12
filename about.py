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
def about(Willie, trigger):
    """Shares basic information on the bot."""
    time.sleep(random.uniform(0, 3))
    Willie.say(u"Hello, my name is %s and I'm a pony! " % Willie.nick +
               u"http://mlpdrawingschool.deviantart.com/gallery/37232754")
    time.sleep(random.uniform(3, 5))
    Willie.say(u"Well, that's not exactly right. I'm speaking to you " +
               u"through an implementation of the Willie bot hosted by " +
               u"tdreyer1.")
    time.sleep(random.uniform(3, 5))
    Willie.say(u"I'm also open source! You can see my source at " +
               u"http://willie.dftba.net/ and my plugins at " +
               u"http://bitbucket.org/tdreyer/fineline")


@commands('bugs', 'bug')
def bugs(Willie, trigger):
    """Shares basic bug reporting information for the bot."""
    time.sleep(random.uniform(0, 3))
    Willie.say(u'[](/derpyshock "Bugs?! I don\'t have any bugs!")')
    time.sleep(random.uniform(4, 6))
    Willie.say(u"But I guess if you think you've found one, you can either " +
               u"message my owner, tdreyer1, or you can make a bug report " +
               u"at https://bitbucket.org/tdreyer/fineline/issues")


@commands('source')
def source(Willie, trigger):
    """Gives links to the bot's source code"""
    time.sleep(random.uniform(0, 3))
    Willie.say('[](/ppnervous "My what?")')
    time.sleep(random.uniform(3, 5))
    Willie.say(u"Well I guess it's okay, since it's you. You can see my " +
               u"source at http://willie.dftba.net/ and my plugins at " +
               u"http://bitbucket.org/tdreyer/fineline")


if __name__ == "__main__":
    print __doc__.strip()
