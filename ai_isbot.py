"""
ai_isbot.py - A Willie module to simulate some simple AI
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import time

random.seed()

def isbot(Willie, trigger):
    """Replies to queries about fineline being a bot"""

    time.sleep(random.uniform(1,2))
    Willie.say(random.choice(("Nope, I'm just fast.",
            "Nah, I just type really fast and know a lot.",
            "What makes you think that?",
            "lolno",
            "Uh.....no?"
            )))
    time.sleep(random.uniform(3,5))
    Willie.say(random.choice(("And I have hooves!",
            "If I were a bot, how come I have hooves?",
            "See? I have hooves! *wiggles hooves*"
            )))
isbot.rule = r'.*$nickname\:?,?\s+Are you a bot|.*$nickname (is )?a bot'
isbot.priority = 'medium'
isbot.rate = 300


if __name__ == "__main__":
    print __doc__.strip()
