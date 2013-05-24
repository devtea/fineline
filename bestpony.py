"""
bestpony.py - A simple, silly module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import time, random

random.seed()

def bestpony(Willie, trigger):
    """Responds with who it thinks is the best pony."""

    if random.uniform(0,3) > 2:
        Willie.say(random.choice(("Well, let's see", "Hmm...", "Uh...",
            "Oh, I know!", "That's easy!")))
        time.sleep(random.uniform(1,3))

    Willie.say(random.choice(("FineLine!", "Me of course!", "I am!")))

    if random.uniform(0,20) > 19:
        time.sleep(random.uniform(3,5))
        Willie.say(r"Okay, just kidding. It's really Pinkie Pie.")


### COMMAND
#Match a command sequence eg !cmd
bestpony.commands = ['bestpony']

#Priorities of 'high', 'medium', and 'low' work
bestpony.priority = 'medium'

#Limit in seconds of users ability to trigger module
bestpony.rate = 30

#Example used in help query to bot for commands
bestpony.example = "user: !bestpony"

if __name__ == "__main__":
    print __doc__.strip()
