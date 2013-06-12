"""
pony.py - A silly Willie module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import timers_slow

def pony(willie, trigger):
    '''Returns pony pic'''
    willie.debug('pony.py', 'Triggered', 'verbose')
    willie.debug('pony.py', trigger.sender, 'verbose')
    timers_slow.cute(willie, trigger.sender, is_timer=False)
pony.commands = ['pony', 'pon[ie]']


if __name__ == "__main__":
    print __doc__.strip()
