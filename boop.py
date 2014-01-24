"""
boop.py - A Willie module that does something
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
#TODO user aliases

#import time
from willie.module import commands
from willie.tools import Nick
import random


_excludes = []
_lists = {}
_front = ['any', 'some']
_back = ['one', 'body', 'pony', 'poni', 'pone']
_anyone = [a + b for a in _front for b in _back]
_boop = [u'boops %s',
         u'sneaks up and boops %s',
         u'licks her hoof and boops %s'
         ]
_self = [u'spins around in circles trying to boop herself']


def setup(bot):
    #do setup stuff
    pass


@commands(u'boop')
def boop(bot, trigger):
    """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis sodales. """
    #print 'Fineline is in this room: %s' % bot.memory['nick_func'](trigger.sender, 'fineline')
    #print 'Nicks in this room: %r' % bot.memory['nick_func'](trigger.sender)
    try:
        target = Nick(trigger.args[1].split()[1])
    except IndexError:
        bot.action(u'boops %s' % trigger.nick)
    else:
        if target == trigger.nick:
            bot.action(random.choice(_boop) % trigger.nick)
        elif target == bot.nick:
            bot.action(random.choice(_self))
        elif target in _anyone:
            target = bot.nick
            nick_list = bot.memory['nick_func'](trigger.sender)
            while target == bot.nick:
                target = random.choice(nick_list)
            bot.action(random.choice(_boop) % target)
        elif target in _excludes:
            bot.say(u"I'm not doing that.")
        elif target in _lists:
            #TODO boop list of people subscribed to list
            pass
        elif bot.memory['nick_func'](trigger.sender, target):
            #TODO get proper nick from memory
            bot.action(random.choice(_boop) % target)
        else:
            bot.reply(u'Sorry, I don\'t see %s around here.' % target)

    '''
    if no arguments or if single argument is 'anybody'
        bot.memory['nick_func'](trigger.source, nick)
        get list of nicks in room
        boop a random one
    else if single argument is everyone
        something something everyone
    else if first or only argument is 'subscribed?'
        for nick in subscriber list
            if nick in room
                add to tmp list
        boop everyone on tmp list w/ message if provided
            format: 'message | names'
    else if single argument
        get list  of nicks in room
        if argument in list
            boop them
        else
            dont
    else
        error
'''


@commands(u'optin')
def optin(bot, trigger):
    pass


@commands(u'optout')
def optout(bot, trigger):
    pass


if __name__ == "__main__":
    print __doc__.strip()
