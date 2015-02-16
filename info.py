# coding=utf8
"""
info.py - Willie Information Module
Copyright 2008, Sean B. Palmer, inamidst.com
Copyright © 2013, Elad Alfassa, <elad@fedoraproject.org>
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import os.path
import re
from urllib.parse import urljoin

from string import Template

from willie.config import ConfigurationError
from willie.logger import get_logger
from willie.module import commands, example, interval, priority, rule

LOGGER = get_logger(__name__)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    # import os.path
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()
try:
    import nicks
except:
    import imp
    import sys
    # import os.path
    try:
        LOGGER.info(log.format("trying manual import of nicks"))
        fp, pathname, description = imp.find_module('nicks', [os.path.join('.', '.willie', 'modules')])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()
try:
    import util
except:
    import imp
    import sys
    # import os.path
    try:
        LOGGER.info(log.format("trying manual import of util"))
        fp, pathname, description = imp.find_module('util', [os.path.join('.', '.willie', 'modules')])
        util = imp.load_source('util', pathname, fp)
        sys.modules['util'] = util
    finally:
        if fp:
            fp.close()

_FILENAME = 'bot_help.html'
_ADMIN_FILENAME = 'bot_help_admin.html'
_html_template = Template('''\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>${title}</title>
    <style>
        .description {
            padding-left: 15px;
        }

        .example {
            color: grey;
            padding-left: 30px;
            padding-top: 5px;
        }
        a {
            border-bottom-width: 1px;
            border-bottom-style: solid;
            text-decoration: none;
            padding-bottom: 0px;
        }
    </style>
</head>
<body>
    <h2>Commands</h2>
    <ul>
${directory}
    </ul>
${body}
</body>
</html>
''')
_section_template = Template('''
    <h2 id="${header}">${header}</h2>
    <p>
        <div class="description">${description}</div>${example}
    </p>''')
_example_template = Template('\n        <div class="example">Example: ${example}</div>')
_directory_section_template = Template('        <li><a href="#${header}">${header}</a></li>')


def setup(bot=None):
    if not bot:
        return

    if bot.config.has_option('help', 'threshold') and not bot.config.help.threshold.isdecimal():  # non-negative integer
        raise ConfigurationError("Attribute threshold of section [help] must be a nonnegative integer")

    bot.memory['help'] = {}

    bot.memory['help']['use_urls'] = False
    if bot.config.has_section('general'):
        if bot.config.has_option('general', 'hosted_domain') \
                and bot.config.has_option('general', 'hosted_path'):
            bot.memory['help']['user_domain'] = urljoin(bot.config.general.hosted_domain, _FILENAME)
            bot.memory['help']['admin_domain'] = urljoin(bot.config.general.hosted_domain, _ADMIN_FILENAME)
            bot.memory['help']['user_path'] = os.path.join(bot.config.general.hosted_path, _FILENAME)
            bot.memory['help']['admin_path'] = os.path.join(bot.config.general.hosted_path, _ADMIN_FILENAME)
            bot.memory['help']['use_urls'] = True
            generate_help_lists(bot)  # Initialize pages
        else:
            raise ConfigurationError("hosted_domain and hosted_path options of section [general] must exist")
    else:
        raise ConfigurationError("hosted_domain and hosted_path options of section [general] must exist")


@interval(600)
def generate_help_lists(bot):
    '''Generates HTML for help pages.'''
    def format_example(example):
        if example:
            return _example_template.substitute(example=example)
        return ''

    # Check that everything is configured for this module
    if not bot.memory['help']['use_urls']:
        return

    reverse_doc = {}
    for i in bot.doc:
        if len(bot.doc[i][0]) == 0:
            desc = bot.doc[i][1] or '[No Description Provided]'
        else:
            desc = ' '.join(bot.doc[i][0])  # that list in the docs is lines of the module's docstring
        if desc not in reverse_doc:
            reverse_doc[desc] = []
        reverse_doc[desc].append(i)

    directory = '\n'.join(
        sorted([_directory_section_template.substitute(
            header=', '.join(sorted(reverse_doc[i])),
            ) for i in reverse_doc if not re.findall(r'\badmin\b|\bwillies?\b|\bowner\b', i, re.I)]))
    admin_directory = '\n'.join(
        sorted([_directory_section_template.substitute(
            header=', '.join(sorted(reverse_doc[i])),
            ) for i in reverse_doc]))
    body = '\n'.join(
        sorted([_section_template.substitute(
            header=', '.join(sorted(reverse_doc[i])),
            description=i,
            example='' if i == bot.doc[reverse_doc[i][0]][1] else format_example(bot.doc[reverse_doc[i][0]][1])
            ) for i in reverse_doc if not re.findall(r'\badmin\b|\bwillies?\b|\bowner\b', i, re.I)]))
    admin_body = '\n'.join(
        sorted([_section_template.substitute(
            header=', '.join(sorted(reverse_doc[i])),
            description=i,
            example='' if i == bot.doc[reverse_doc[i][0]][1] else format_example(bot.doc[reverse_doc[i][0]][1])
            ) for i in reverse_doc]))
    html = _html_template.substitute(
        title='command help',
        directory=directory,
        body=body)
    admin_html = _html_template.substitute(
        title='command help',
        directory=admin_directory,
        body=admin_body)

    try:
        with open(bot.memory['help']['user_path'], 'r') as f:
            previous_html = ''.join(f.readlines())
    except IOError:
        previous_html = ''
        LOGGER.warning(log.format('IO error grabbing previous user help file contents. File may not exist yet'))
    try:
        with open(bot.memory['help']['admin_path'], 'r') as f:
            previous_admin_html = ''.join(f.readlines())
    except IOError:
        previous_admin_html = ''
        LOGGER.warning(log.format('IO error grabbing previous admin help file contents. File may not exist yet'))

    if previous_html != html:
        LOGGER.info(log.format('User help file is different, writing.'))
        with open(bot.memory['help']['user_path'], 'w') as f:
            f.write(html)

    if previous_admin_html != admin_html:
        LOGGER.info(log.format('Admin help file is different, writing.'))
        with open(bot.memory['help']['admin_path'], 'w') as f:
            f.write(admin_html)


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
            threshold = int(bot.config.help.threshold)
        else:
            threshold = 3

        if name in bot.doc:
            if len(bot.doc[name][0]) + (1 if bot.doc[name][1] else 0) > threshold:
                if trigger.nick != trigger.sender:  # don't say that if asked in private
                    bot.reply('The documentation for this command is too long; I\'m sending it to you in a private message.')
                msgfun = lambda l: bot.msg(trigger.nick, l)
            else:
                msgfun = bot.reply

            for line in bot.doc[name][0]:
                msgfun(line)
            if bot.doc[name][1]:
                msgfun('e.g. ' + bot.doc[name][1])


@commands('commands')
@priority('low')
def commands(bot, trigger):
    """Return a list of bot's commands"""
    if trigger.admin:
        bot.reply("Check your messages, %s" % trigger.nick)
        bot.msg(trigger.nick, "You can see a list of my admin commands at %s" % bot.memory['help']['admin_domain'])
    else:
        bot.reply("You can see a list of my user commands at %s" % bot.memory['help']['user_domain'])


@rule('$nick' r'(?i)help(?:[?!]+)?$')
@priority('low')
def help2(bot, trigger):
    response = (
        'Hi, I\'m a bot. Say "!commands" to me for a list ' +
        'of my commands, or see http://willie.dftba.net for more ' +
        'general details. My owner is %s.'
    ) % bot.config.owner
    bot.reply(response)


if __name__ == '__main__':
    print(__doc__.strip())
