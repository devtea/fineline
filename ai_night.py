"""
ai_night.py - A Willie module to simulate some simple AI
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import time

random.seed()

def night(Willie, trigger):
    """Responds to people saying good night"""
    message = random.choice(("Goodnight","'Night","Later","Bye"))
    punctuation = random.choice((".","","!"))
    # Test statment to filter negetive statements
    Willie.debug("ai_night.py:night", trigger.bytes, "verbose")
    # Use a set intersection to filter triggering lines by keyword
    if not set(trigger.args[1].lower().split()).intersection(set(['not','no','at'])):
        time.sleep(1)
        if random.uniform(0,1) > 0.5:
            Willie.reply(message + punctuation)
        else:
            Willie.say(message + " " + trigger.nick + punctuation)
prefix = r"($nickname\:?,?\s+)"
meat = r"((good|g)?\s?'?(night|bye)|(later(s?)))"
all = r"(all|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
        "folks|guys|peoples?|$nickname)"
to_fineline = prefix + meat
to_all = r".*?" + meat + r",?\s+" + all
universal = r".*?((time (for me)?\s?(to|for)\s?((go to)|(head))?\s?(to )?" + \
            "(bed|sleep))|" + \
            "(I'?m ((((going to)|(gonna)) ((go)|(head off))?)|(heading off))\s?(to )?(bed|sleep|crash|(pass out))))"
night.rule = r"(" + to_fineline + r")|" + \
        r"(" + to_all + r")|" + \
        r"(" + universal + r")"
night.priority = 'high'
night.rate = 1000

if __name__ == "__main__":
    print __doc__.strip()
