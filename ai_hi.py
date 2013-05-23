"""
ai_hi.py - A Willie module to simulate some simple AI
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random, time

random.seed()

def hi(Willie, trigger):
    """Replies to greetings, usually."""

    if random.uniform(0,100)>3:
        message = random.choice(("Hi","Hello","Yo","Hey","Ahoy"))
        wait = random.uniform(0,5)
        punctuation = random.choice((".","","!"))

        time.sleep(wait)
        Willie.say(trigger.nick + ": " + message + punctuation)

hi_terms = "(hi|hey|hello|ahoy|yo|sup)"
hi.rule = r'$nickname\:?,?\s+' + hi_terms + r'|' + hi_terms + r',?\s+$nickname'
hi.priority = 'medium'
hi.thread = False
hi.rate = 300

if __name__ == "__main__":
    print __doc__.strip()
