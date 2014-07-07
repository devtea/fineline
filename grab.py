"""
grab.py - A simple willie module to auto quote people
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from willie.module import commands, rule, example
from willie.tools import Nick
import threading

# Nicks to exclude
_excludes = ['hushmachine', 'hushmachine_']


def setup(bot):
    bot.memory['grab'] = {}
    bot.memory['grablock'] = threading.Lock()


@example(u'!grab tdreyer1')
@commands('grab', 'grabart', 'grabarttip', 'grabtip')
def grab(bot, trigger):
    '''Grabs the last line from a user and !addquotes it.'''
    try:
        target = Nick(trigger.args[1].split()[1])
    except IndexError:
        bot.say(u'Grab who?')
    else:
        bot.memory['grablock'].acquire()
        try:
            if target == trigger.nick:
                bot.say(u"Eww, don't grab yourself in public!")
            elif target == bot.nick:
                bot.say(u"Hey, don't grab me!")
            elif target in _excludes:
                bot.say(u"I'm not grabbing that.")
            elif target in bot.memory['grab']:
                if len(trigger.bytes.split()[0]) == len('!grab'):
                    bot.say(u'!addquote <%s> %s' % (target, bot.memory['grab'][target]))
                else:
                    bot.say(u'!addarttip <%s> %s' % (target, bot.memory['grab'][target]))
            else:
                bot.say(u'Sorry, nothing to grab!')
        finally:
            bot.memory['grablock'].release()


@rule('.*')
def recent_watcher(bot, trigger):
    bot.memory['grablock'].acquire()
    try:
        if trigger.sender.startswith('#'):
            if trigger.bytes.startswith('\001ACTION'):
                bot.memory['grab'][Nick(trigger.nick)] = '%s%s' % (trigger.nick, trigger.bytes[7:])
            else:
                bot.memory['grab'][Nick(trigger.nick)] = trigger.bytes
    finally:
        bot.memory['grablock'].release()


if __name__ == "__main__":
    print __doc__.strip()
