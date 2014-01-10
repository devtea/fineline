"""
info.py - Willie Information Module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

from willie.module import commands, rule, example, priority

_EXCLUDE = ['#reddit-mlpds']


@rule(u'$nick' '(?i)(help|doc) +([A-Za-z]+)(?:\?+)?$')
@example(u'!help seen')
@commands(u'help')
@priority(u'low')
def doc(bot, trigger):
    """Shows a command's documentation, and possibly an example."""
    if not trigger.group(2):
        if trigger.sender in _EXCLUDE:
            return
        bot.reply('Say !help <command> (for example !help seen) to get help for a command, or !commands for a list of commands.')
    else:
        name = trigger.group(2)
        name = name.lower()

        if (name in bot.doc
                and not bot.doc[name][0].startswith(u"ADMIN")):
            bot.reply(bot.doc[name][0])
            if bot.doc[name][1]:
                bot.say(u'e.g. ' + bot.doc[name][1])


@commands(u'commands')
@priority(u'low')
def commands(bot, trigger):
    """Return a list of the bot's commands"""
    if trigger.owner:
        names = u', '.join(sorted(bot.doc.iterkeys()))
    else:
        cmds = [i for i in sorted(bot.doc.iterkeys())
                if not bot.doc[i][0].startswith(u"ADMIN")
                and i not in [u'newoplist',
                              u'listops',
                              u'listvoices',
                              u'blocks',
                              u'part',
                              u'quit'
                              ]  # bad hack for filtering admin cmds
                ]
        names = u', '.join(sorted(cmds))
    bot.reply(u'Commands I recognise: ' + names + u'.')
    bot.reply(u"For help, do '!help example' where example is the " +
              u"name of the command you want help for.")


@rule('$nick' r'(?i)help(?:[?!]+)?$')
@priority('low')
def help(bot, trigger):
    response = (
        u'Hi! I\'m %s and I\'m a pony. Say "!commands" to me in private ' +
        u'for a list of the things I can do. Say hi to my master, %s!'
    ) % (bot.nick, bot.config.owner)
    bot.reply(response)


if __name__ == '__main__':
    print __doc__.strip()
