"""
ai_night.py - A Willie module to simulate some simple AI
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random

def night(Willie, trigger):
    """Responds to people saying good night"""

    message = random.choice(("Goodnight","'Night","Later","Bye"))
    punctuation = random.choice((".","","!"))

    #Replies cause the bot to reply to the triggered message
    #if statment to filter negetive statements
    if ('not' and 'no') not in trigger.bytes:
        Willie.reply(message + punctuation)

prefix = r"($nickname:?,?\s+)"
meat = r"((good)?\s?'?(night|bye))|(later)"
all = r"all|every\s?(body|one|pony|pone|poni)|mlpds"
to_fineline = prefix + meat
to_all = r".*\s" + meat + r"\s+" + all
universal = r".*?(time (for me)?\s?(to|for)\s?(go to)?\s?(bed|sleep))"

night.rule = r"(" + to_fineline + r")|" + \
        r"(" + to_all + r")|" + \
        r"(" + universal + r")"

#Priorities of 'high', 'medium', and 'low' work
night.priority = 'high'

#Willie is multithreaded by default.
#night.thread = False

#Limit in seconds of users ability to trigger module
night.rate = 1000

if __name__ == "__main__":
    print __doc__.strip()
