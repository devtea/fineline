# coding=utf8
"""
info.py - Willie Information Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import unicode_literals

import os.path
from willie.module import commands, rule, example, priority
from willie.tools import iterkeys

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import util
except:
    import imp
    import sys
    try:
        print("trying manual import of util")
        fp, pathname, description = imp.find_module('util', [os.path.join('.', '.willie', 'modules')])
        util = imp.load_source('util', pathname, fp)
        sys.modules['util'] = util
    finally:
        if fp:
            fp.close()


def setup(bot=None):
    if not bot:
        return

    if bot.config.has_option('help', 'threshold') and not bot.config.help.threshold.isdecimal():#non-negative integer
        from willie.config import ConfigurationError
        raise ConfigurationError("Attribute threshold of section [help] must be a nonnegative integer")


@rule('$nick' '(?i)(help|doc) +([A-Za-z]+)(?:\?+)?$')
@example('!help seen')
@commands('help')
@priority('low')
def help(bot, trigger):
    """Shows a command's documentation, and possibly an example."""
    if not trigger.group(2):
        if util.exists_quieting_nick(bot, trigger.sender):
            return
        bot.reply('Say !help <command> (for example !help seen) to get help for a command, or !commands for a list of commands.')
    else:
        name = trigger.group(2)
        name = name.lower()

        if bot.config.has_option('help', 'threshold'):
            threshold=int(bot.config.help.threshold)
        else:
            threshold=3

        if name in bot.doc:
            if len(bot.doc[name][0]) + (1 if bot.doc[name][1] else 0) > threshold:
                if trigger.nick != trigger.sender: #don't say that if asked in private
                    bot.reply('The documentation for this command is too long; I\'m sending it to you in a private message.')
                msgfun=lambda l: bot.msg(trigger.nick,l)
            else:
                msgfun=bot.reply

            for line in bot.doc[name][0]:
                msgfun(line)
            if bot.doc[name][1]:
                msgfun('e.g. ' + bot.doc[name][1])


@commands('commands')
@priority('low')
def commands(bot, trigger):
    """Return a list of bot's commands"""
    names = ', '.join(sorted(iterkeys(bot.doc)))
    if not trigger.is_privmsg:
        bot.reply("I am sending you a private message of all my commands!")
    bot.msg(trigger.nick, 'Commands I recognise: ' + names + '.', max_messages=10)
    bot.msg(trigger.nick, ("For help, do '%s: help example' where example is the " +
                    "name of the command you want help for.") % bot.nick)


@rule('$nick' r'(?i)help(?:[?!]+)?$')
@priority('low')
def help2(bot, trigger):
    response = (
        'Hi, I\'m a bot. Say ".commands" to me in private for a list ' +
        'of my commands, or see http://willie.dftba.net for more ' +
        'general details. My owner is %s.'
    ) % bot.config.owner
    bot.reply(response)


if __name__ == '__main__':
    print __doc__.strip()
