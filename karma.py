"""
karma.py - A willie module to keep track of "points" for arbitrary things
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import threading
import time

from willie.module import commands, example, rule, priority

def setup(willie):
    if 'karma_lock' not in willie.memory:
        willie.memory['karma_lock'] = threading.Lock()
    if 'karma' not in willie.memory:
        willie.memory['karma'] = {}
    if 'karma_time' not in willie.memory:
        willie.memory['karma_time'] = {}

@priority(u'low')
@rule(u'.*')
def karmaRule(willie, trigger):
    if trigger.sender[0] != '#':
        return
    obj = trigger.args[1].split()
    if not obj:
        return
    obj = obj[0]
    if len(obj) < 3:
        return
    shortobj = obj[:-2]
    
    if obj.endswith("++") and timecheck(willie, trigger):
        modkarma(willie, shortobj, 1)
    elif obj.endswith("--") and timecheck(willie, trigger):
        modkarma(willie, shortobj, 1)

def timecheck(willie, trigger):
    willie.memory['karma_lock'].acquire()
    try:
        if trigger.sender in willie.memory['karma_time'] and time.time() < willie.memory['karma_time'][trigger.sender] + 60:
	    willie.reply(u"You just used karma! You can't use it again for a bit.")
	    return False
	willie.memory['karma_time'][trigger.sender] = time.time()
        return True
    finally:
        willie.memory['karma_lock'].release()

@commands('karma')
@example(u'!karma fzoo')
def karma(willie, trigger):
    modkarma(willie, trigger.args[1].split()[1], 0)

def modkarma(willie, obj, amount):
    willie.memory['karma_lock'].acquire()
    try:
        if obj in willie.memory['karma']:
	    willie.memory['karma'][obj] += amount
	else:
	    willie.memory['karma'][obj] = amount
	
	willie.reply("Karma for %s is at %i" % (obj, willie.memory['karma'][obj]))
    finally:
        willie.memory['karma_lock'].release()


if __name__ == "__main__":
    print __doc__.strip()
