"""
grab.py - A simple willie module to auto quote people
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import threading
import time

from willie.logger import get_logger
from willie.module import commands, rule, example
from willie.tools import Identifier

# Bot framework is stupid about importing, so we need to do silly stuff
try:
    import log
except:
    import sys
    import os.path
    sys.path.append(os.path.join('.', '.willie', 'modules'))
    import log
    if 'log' not in sys.modules:
        sys.modules['log'] = log
try:
    import colors
except:
    import sys
    import os.path
    sys.path.append(os.path.join('.', '.willie', 'modules'))
    import colors
    if 'colors' not in sys.modules:
        sys.modules['colors'] = colors
try:
    import util
except:
    import sys
    import os.path
    sys.path.append(os.path.join('.', '.willie', 'modules'))
    import util
    if 'util' not in sys.modules:
        sys.modules['util'] = util

# Nicks to exclude
_excludes = ['oppobot', 'hushmachine', 'hushmachine_', 'hushrobot', 'finelinefan']
LOGGER = get_logger(__name__)


def setup(bot):
    if 'grab' not in bot.memory:
        bot.memory['grab'] = {}
    if 'lock' not in bot.memory['grab']:
        bot.memory['grab']['lock'] = threading.Lock()
    if 'list' not in bot.memory['grab']:
        bot.memory['grab']['list'] = {}
    if 'request' not in bot.memory['grab']:
        bot.memory['grab']['request'] = {}


@example('!grab username')
@commands('grab', 'grabart', 'grabarttip', 'grabtip')
def grab(bot, trigger):
    '''Grabs the last line from a user and !addquotes it.'''
    if not trigger.sender.startswith('#'):
        return
    try:
        target = Identifier(trigger.args[1].split()[1])
    except IndexError:
        bot.say('Grab who?')
    else:
        if target == trigger.nick or target.lower() == 'me':
            bot.say("Eww, don't grab yourself in public!")
            return
        elif target == bot.nick:
            bot.say("Hey, don't grab me!")
            return
        elif util.ignore_nick(bot, target):
            bot.say("I'm not grabbing that.")
            return

        if trigger.nick in bot.memory['grab']['request']:
            # There is already a request pending
            with bot.memory['grab']['lock']:
                if target == bot.memory['grab']['request'][trigger.nick][0]:
                    bot.say(bot.memory['grab']['request'][trigger.nick][1])
                    try:
                        del bot.memory['grab']['request'][trigger.nick]
                    except KeyError:
                        # Nick already removed, do nothing.
                        pass
                else:
                    bot.reply('Sorry, you already have a grab request pending for %s' %
                              bot.memory['grab']['request'][trigger.nick][0])
        else:
            # This is a new request
            if target in bot.memory['grab']['list']:
                with bot.memory['grab']['lock']:
                    # create text for either normal lines or /me
                    if bot.memory['grab']['list'][target][0]:
                        grab_text = '* %s %s' % (target, bot.memory['grab']['list'][target][1])
                    else:
                        grab_text = '<%s> %s' % (target, bot.memory['grab']['list'][target][1])

                    if len(trigger.split()[0]) == len('!grab'):
                        bot.memory['grab']['request'][trigger.nick] = (target, '!addquote %s' % grab_text)
                    else:
                        bot.memory['grab']['request'][trigger.nick] = (target, '!addarttip %s' % grab_text)
                    time.sleep(3)
                    bot.reply(
                        "Yo're trying to grab '%s' - To confirm, repeat this command within 15 seconds." %
                        colors.colorize(grab_text, ['orange']))
                time.sleep(15)
                with bot.memory['grab']['lock']:
                    # Reset request
                    try:
                        del bot.memory['grab']['request'][trigger.nick]
                    except KeyError:
                        # Nick already removed, do nothing.
                        pass
            else:
                # bot.say('Sorry, nothing to grab!')
                pass


@rule('.*')
def recent_watcher(bot, trigger):
    # bot.memory['grab']['list'][nick] = (is_action, text)
    with bot.memory['grab']['lock']:
        if trigger.sender.startswith('#'):
            if trigger.startswith('\001ACTION'):
                bot.memory['grab']['list'][Identifier(trigger.nick)] = (True, trigger[8:])
            else:
                bot.memory['grab']['list'][Identifier(trigger.nick)] = (False, trigger)


@commands('grab_clear')
def clear(bot, trigger):
    '''Clears the recent history for grabs. Admin only.'''
    if not trigger.owner:
        return
    bot.memory['grab'] = {}
    bot.memory['grab']['lock'] = threading.Lock()
    bot.memory['grab']['list'] = {}
    bot.memory['grab']['request'] = {}


if __name__ == "__main__":
    print(__doc__.strip())
