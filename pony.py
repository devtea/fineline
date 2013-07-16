"""
pony.py - A silly Willie module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import slow_room

from willie.module import commands


@commands(u'pony', u'pon[ie]')
def pony(willie, trigger):
    '''Returns pony pic'''
    willie.debug(u'pony.py', u'Triggered', u'verbose')
    willie.debug(u'pony.py', trigger.sender, u'verbose')
    slow_room.cute(willie, trigger.sender, is_timer=False)


if __name__ == "__main__":
    print __doc__.strip()
