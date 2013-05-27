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
    #if ('not' and 'no' and 'at') not in trigger.bytes:
    if (('not' not in trigger.bytes)  and ('no' not in trigger.bytes) and
            ('at' not in trigger.bytes)):
        time.sleep(1)
        if random.uniform(0,1) > 0.5:
            Willie.reply(message + punctuation)
        else:
            Willie.say(message + " " + trigger.nick + punctuation)
prefix = r"($nickname\:?,?\s+)"
meat = r"((good|g)?\s?'?(night|bye)|(later))"
all = r"(all|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
        "folks|guys|peoples?|$nickname)"
to_fineline = prefix + meat
to_all = r".*?" + meat + r",?\s+" + all
universal = r".*?((time (for me)?\s?(to|for)\s?((go to)|(head))?\s?(to )?" + \
        "(bed|sleep))|" + \
        "(I'?m going to (go to)?\s?(bed|sleep|crash|(pass out))))"
night.rule = r"(" + to_fineline + r")|" + \
        r"(" + to_all + r")|" + \
        r"(" + universal + r")"
# Priorities of 'high', 'medium', and 'low' work
night.priority = 'high'
# Willie is multithreaded by default.
#night.thread = False
# Limit in seconds of users ability to trigger module
night.rate = 1000

if __name__ == "__main__":
    print __doc__.strip()
