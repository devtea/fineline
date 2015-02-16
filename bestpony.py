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
def bestpony(bot, trigger):
    """Responds with the best pony."""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    if random.uniform(0, 3) > 2:
        bot.say(random.choice([
            "Well, let's see",
            "Hmm...",
            "Uh...",
            "Oh, I know!",
            "That's easy!"]))
        time.sleep(random.uniform(1, 3))
    bot.say(random.choice([
        bot.nick + "!",
        "I, of course!",
        "I am!"]))
    if random.uniform(0, 20) > 19:
        time.sleep(random.uniform(3, 5))
        bot.say("Okay, just kidding. It's really Pinkie Pie.")


if __name__ == "__main__":
    print(__doc__.strip())
