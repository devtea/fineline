"""
about.py - A simple Willie information module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import random, time

random.seed()



def about(Willie, trigger):
    """Shares basic information on the bot."""

    time.sleep(random.uniform(0,3))
    Willie.say(r"Hello, my name is %s and I'm a pony!" % Willie.nick)
    time.sleep(random.uniform(3,5))
    Willie.say(r"I'm speaking to you through an implementation of the Willie " +
            "bot hosted by tdreyer1.")
    time.sleep(random.uniform(3,5))
    Willie.say(r"I'm also open source! You can see my source at " +
            "http://willie.dftba.net/ and my plugins at " +
            "http://bitbucket.org/tdreyer/fineline")
about.commands = ['about']
about.priority = 'medium'
about.rate = 300



def bugs(Willie, trigger):
    """Shares basic bug reporting information for the bot."""

    time.sleep(random.uniform(0,3))
    Willie.say('[](/derpyshock "Bugs?! I don\'t have any bugs!")')
    time.sleep(random.uniform(4,6))
    Willie.say(r"But I guess if you think you've found one, you can either " +
        "message my owner, tdreyer1, or you can make a bug report at " +
        "https://bitbucket.org/tdreyer/fineline/issues")
bugs.commands = ['bugs','bug']
bugs.priority = 'medium'
bugs.rate = 300



def source(Willie, trigger):
    """Gives links to the bot's source code"""

    time.sleep(random.uniform(0,3))
    Willie.say('[](/ajblush "My what?")')
    time.sleep(random.uniform(3,5))
    Willie.say(r"Well I guess it's okay, since it's you. You can see my source at " +
            "http://willie.dftba.net/ and my plugins at " +
            "http://bitbucket.org/tdreyer/fineline")
source.commands = ['source']
source.priority = 'medium'
source.rate = 300


if __name__ == "__main__":
    print __doc__.strip()
