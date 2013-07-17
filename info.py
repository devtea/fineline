"""
info.py - Willie Information Module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

from willie.module import commands, rule, example, priority


@rule(u'$nick' '(?i)(help|doc) +([A-Za-z]+)(?:\?+)?$')
@example(u'!help seen')
@commands(u'help')
@priority(u'low')
def doc(willie, trigger):
    """Shows a command's documentation, and possibly an example."""
    name = trigger.group(2)
    name = name.lower()

    if (name in willie.doc
            and not willie.doc[name][0].startswith(u"ADMIN")):
        willie.reply(willie.doc[name][0])
        if willie.doc[name][1]:
            willie.say(u'e.g. ' + willie.doc[name][1])


@commands(u'commands')
@priority(u'low')
def commands(willie, trigger):
    """Return a list of Willie's commands"""
    if trigger.owner:
        names = u', '.join(sorted(willie.doc.iterkeys()))
    else:
        cmds = [i for i in sorted(willie.doc.iterkeys())
                if not willie.doc[i][0].startswith(u"ADMIN")
                and i not in [u'newoplist',
                              u'listops',
                              u'listvoices',
                              u'blocks',
                              u'part',
                              u'quit'
                              ]  # bad hack for filtering admin cmds
                ]
        names = u', '.join(sorted(cmds))
    willie.reply(u'Commands I recognise: ' + names + u'.')
    willie.reply((u"For help, do '%s: help example?' where example is the " +
                  u"name of the command you want help for.") % willie.nick)


@rule('$nick' r'(?i)help(?:[?!]+)?$')
@priority('low')
def help(willie, trigger):
    response = (
        u'Hi! I\'m %s and I\'m a pony. Say ".commands" to me in private ' +
        u'for a list of the things I can do. Say hi to my master, %s!'
    ) % (willie.nick, willie.config.owner)
    willie.reply(response)


if __name__ == '__main__':
    print __doc__.strip()
