"""
ai_isbot.py - A Willie module to simulate some simple AI
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random, time

random.seed()

def isbot(Willie, trigger):
    """Replies to queries about fineline being a bot"""
    nomessage = random.choice(("Nope, I'm just fast",
        "Nah, I just type fast and know a lot"))
    afterthought = random.choice(("Oh, and I have hooves...",
        "And I might have hooves..."))
    punctuation = random.choice((".","","!"))
    wait = random.uniform(0,2)
    pause = random.uniform(2,5)

    time.sleep(wait)
    Willie.say(nomessage + punctuation)
    time.sleep(pause)
    Willie.say(afterthought)

isbot.rule = r'.*$nickname\:?,?\s+Are you a bot|.*Is $nickname a bot'
isbot.priority = 'medium'
isbot.thread = False
isbot.rate = 300

if __name__ == "__main__":
    print __doc__.strip()
