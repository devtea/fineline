"""
ping.py - A simple ping module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

def ping(Willie, trigger):
    """Responds to a user's ping"""

    Willie.say(r'Pony!')
# Match a command sequence eg !cmd
ping.commands = ['ping']

# Priorities of 'high', 'medium', and 'low' work
ping.priority = 'high'

# Willie is multithreaded by default.
#template.thread = False

# Limit in seconds of users ability to trigger module
ping.rate = 60



if __name__ == "__main__":
    print __doc__.strip()
