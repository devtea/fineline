"""
info.py - Willie Information Module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

def doc(willie, trigger):
    """Shows a command's documentation, and possibly an example."""
    name = trigger.group(2)
    name = name.lower()

    if willie.doc.has_key(name) and not willie.doc[name][0].startswith("ADMIN"):
        willie.reply(willie.doc[name][0])
        if willie.doc[name][1]:
            willie.say('e.g. ' + willie.doc[name][1])
doc.rule = ('$nick', '(?i)(help|doc) +([A-Za-z]+)(?:\?+)?$')
doc.example = '$nickname: doc tell?'
doc.priority = 'low'


def commands(willie, trigger):
    """Return a list of Willie's commands"""
    if trigger.owner:
        names = ', '.join(sorted(willie.doc.iterkeys()))
    else:
        cmds = [i for i in sorted(willie.doc.iterkeys())
                if not willie.doc[i][0].startswith("ADMIN")
                and i not in [
                    'newoplist',
                    'listops',
                    'listvoices',
                    'blocks',
                    'part',
                    'quit'
                    ]  #bad hack for filtering admin cmds
                ]
        names = ', '.join(sorted(cmds))
    willie.reply('Commands I recognise: ' + names + '.')
    willie.reply(("For help, do '%s: help example?' where example is the " +
                    "name of the command you want help for.") % willie.nick)
commands.commands = ['commands']
commands.priority = 'low'


def help(willie, trigger):
    response = (
        'Hi, I\'m a bot. Say ".commands" to me in private for a list ' +
        'of my commands, or see http://willie.dftba.net for more ' +
        'general details. My owner is %s.'
    ) % willie.config.owner
    willie.reply(response)
help.rule = ('$nick', r'(?i)help(?:[?!]+)?$')
help.priority = 'low'

if __name__ == '__main__':
    print __doc__.strip()
