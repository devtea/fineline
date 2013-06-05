"""
ai_hi.py - A Willie module to simulate some simple AI
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import time

random.seed()

def hi(Willie, trigger):
    """Replies to greetings."""
    message = random.choice(("Hi","Hello","Yo","Hey","Ahoy"))
    punctuation = random.choice((".","","!"))
    time.sleep(random.uniform(0,3))
    if random.uniform(0,1) > 0.5:
        Willie.reply(message + punctuation)
    else:
        Willie.say(message + " " + trigger.nick + punctuation)
prefix = r"($nickname[:,]?\s+)"
meat = r"(hello|hi|ahoy|sup|hey|yo|afternoon|morning)"
all = r"(all|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
        "folks|guys|peoples?|$nickname)"
to_fineline = prefix + meat + '([.!\s]?$)'
to_all =  meat + r"[,]?\s+" + all + '([.!\s]?$)'
# Rules allow regex matches to PRIVMSG
hi.rule = r"(" + to_fineline + r")|" + \
        r"(" + to_all + r")"
hi.priority = 'medium'
hi.rate = 300

if __name__ == "__main__":
    print __doc__.strip()
