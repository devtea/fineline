"""
ping.py - A simple ping module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

def ping(Willie, trigger):
    """Responds to a user's ping"""
    Willie.say(r'Pony!')

ping.commands = ['ping']
ping.priority = 'high'
ping.rate = 30
ping.example = r'user: !ping  | FineLine: Pony!'

if __name__ == "__main__":
    print __doc__.strip()
