"""
boop.py - A Willie module that does something
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
#TODO user aliases
#TODO add database access
#TODO add memory lock

#import time
from willie.module import commands
from willie.tools import Nick
import random


_excludes = []
_lists = {}
_listexclude = ['sex', 'fucking', 'life', 'death', 'money', 'all', 'everything']
_front = ['any', 'some']
_back = ['one', 'body', 'pony', 'poni', 'pone']
_anyone = [a + b for a in _front for b in _back]
_everyone = ['every' + b for b in _back]
#TODO add everyone option
_boop = [u'boops %s',
         u'boops %s http://i.imgur.com/ruiIBf5.gif',
         u'boops %s http://i.imgur.com/QlSFlMK.gif',
         u'boops %s http://i.imgur.com/nra4yDL.gif',
         u'boops %s http://i.imgur.com/gkcRoDW.gif',
         u'boops %s just a bit too hard http://i.imgur.com/Jz6jS.gif',
         u'boops %s... politely... http://i.imgur.com/nRwXn.gif',
         u'sneaks up and boops %s',
         u'licks her hoof and boops %s',
         u'boops %s on the nose',
         u'trips and accidentally boops %s in the eye',
         u'gently boops %s on the lips',
         u'gets a little too excited and boops %s out the window',
         u'boops %s through the wall',
         u'"accidentally" boops %s on the plot...',
         u'boops %s hard, over and over http://i.imgur.com/1iCb1.gif',
         u'boops %s before realizing she stepped in something smelly earlier...',
         u'giggles and boops %s',
         u'sticks her tongue out at %s instead',
         u'blows a raspberry at %s instead',
         u'takes one look at %s and runs away',
         u'tries to boop %s, but... http://i.imgur.com/3mFn5YW.gif',
         u'boops %s again, and again, and again, and again... http://i.imgur.com/PC6mBEv.gif'
         ]
_self = [u'spins around in circles trying to boop herself http://i.imgur.com/igq9Mio.gif',
         u'looks funny as she crosses her eyes and tries to boop herself',
         u'pulls a mirror out of nowhere and boops her reflection']


def setup(bot):
    #do setup stuff
    pass


@commands(u'boop')
def boop(bot, trigger):
    """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis sodales. """
    #print 'Fineline is in this room: %s' % bot.memory['nick_func'](trigger.sender, 'fineline')
    #print 'Nicks in this room: %r' % bot.memory['nick_func'](trigger.sender)
    #TODO make sure there are no hostname collisions
    try:
        target = bot.memory['NickPlus'](trigger.args[1].split()[1])
    except IndexError:
        bot.action(random.choice(_boop) % trigger.nick)
    else:
        if target == trigger.nick or target.lower() in ['me', 'myself']:
            bot.action(random.choice(_boop) % trigger.nick)
        elif target == bot.nick or target.lower() in ['yourself', 'you']:
            bot.action(random.choice(_self))
        elif target in _anyone:
            target = bot.nick
            nick_list = bot.memory['nick_func'](trigger.sender)
            while target == bot.nick:
                target = random.choice(nick_list)
            bot.action(random.choice(_boop) % target)
        elif target in _excludes:
            bot.say(u"I'm not doing that.")
        elif bot.memory['nick_func'](trigger.sender, target):
            #TODO get proper nick from memory
            #TODO small chance to boop random person
            bot.action(random.choice(_boop) % target)
        #TODO modify this to allow multi word list names
        elif target in _lists and len(_lists[target]) > 0:
            #TODO allow freeform message in boop
            msg = 'boops '
            for name in _lists:
                msg = "%s %s," % (msg, name)
            msg = msg.strip(',')
            msg = "%s %s" % (msg, '| "%s"')
            bot.action(msg)
        else:
            bot.reply(u'Sorry, I don\'t see %s around here.' % target)


@commands(u'optin')
def optin(bot, trigger):
    try:
        #TODO modify this to allow multi word list names
        target = trigger.args[1].split()[1].lower()
        print target
    except IndexError:
        bot.reply("You must specify a list to opt into.")
    else:
        if target in _listexclude:
            bot.reply(u'You can\'t opt into that...')
            return
        elif target in _lists and Nick(trigger.nick) not in _lists[target]:
            _lists[target].append(bot.memory['NickPlus'](trigger.nick, trigger.host))
        else:
            _lists[target] = [bot.memory['NickPlus'](trigger.nick)]
            bot.reply('You\'ve been added to the \'%s\' list.' % target)


@commands(u'optout')
def optout(bot, trigger):
    try:
        #TODO modify this to allow multi word list names
        target = trigger.args[1].split()[1].lower()
        print target
    except IndexError:
        bot.reply("You must specify a list to opt out of.")
    else:
        name = bot.memory['NickPlus'](trigger.nick)
        if target in _lists and name in _lists[target]:
            _lists[target].remove(name)
            bot.reply('You have been removed from the \'%s\' list.' % target)
        elif target in ['all', 'everything']:
            for i in _lists:
                try:
                    _lists[i].remove(name)
                except:
                    pass
            bot.reply('You have been removed from the all lists.')
        else:
            bot.reply('That list does not exist.')


if __name__ == "__main__":
    print __doc__.strip()
