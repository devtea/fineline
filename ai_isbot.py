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
        "Nah, I just type fast and know a lot",
        "What makes you think that?",
        "Uh.....no?"))
    afterthought = random.choice(("Oh, and I have hooves...",
        "And I might have hooves...",
        "See? I have hooves! *wiggles hooves*"))
    punctuation = random.choice((".","","!"))

    time.sleep(random.uniform(0,2))
    Willie.say(nomessage + punctuation)

    time.sleep(random.uniform(2,5))
    Willie.say(afterthought)
# Rules allow regex matches to PRIVMSG
isbot.rule = r'.*$nickname\:?,?\s+Are you a bot|.*$nickname (is )?a bot'

# Priorities of 'high', 'medium', and 'low' work
isbot.priority = 'medium'

# Willie is multithreaded by default.
#isbot.thread = False

# Limit in seconds of users ability to trigger module
isbot.rate = 300



if __name__ == "__main__":
    print __doc__.strip()
