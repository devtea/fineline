"""
bestpony.py - A simple, silly module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import time
import random

from willie.module import commands

random.seed()


@commands('bestpony')
def bestpony(Willie, trigger):
    """Responds with who it thinks is the best pony."""

    if random.uniform(0, 3) > 2:
        Willie.say(random.choice([u"Well, let's see",
                                  u"Hmm...",
                                  u"Uh...",
                                  u"Oh, I know!",
                                  u"That's easy!"
                                  ]))
        time.sleep(random.uniform(1, 3))

    Willie.say(random.choice((Willie.nick + '!', "I, of course!", "I am!")))

    if random.uniform(0, 20) > 19:
        time.sleep(random.uniform(3, 5))
        Willie.say("Okay, just kidding. It's really Pinkie Pie.")


if __name__ == "__main__":
    print __doc__.strip()
