"""
util.py - A Willie module that provides importable functions for other modules
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import threading

from willie.logger import get_logger

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
    import nicks
except:
    import sys
    import os.path
    sys.path.append(os.path.join('.', '.willie', 'modules'))
    import nicks
    if 'nicks' not in sys.modules:
        sys.modules['nicks'] = nicks

LOGGER = get_logger(__name__)


def setup(bot):
    ignore_list = []
    quiet_list = []
    ignore_whitelist = []
    quiet_whitelist = []
    if bot.config.has_section('general'):
        if bot.config.has_option('general', 'input_ignore'):
            ignore_list = [nicks.NickPlus(i.split("#")[0], i.split("#")[1])
                           if len(i.split("#")) > 1
                           else nicks.NickPlus(i)
                           for i in bot.config.general.get_list('input_ignore')]
        if bot.config.has_option('general', 'presence_quieters'):
            quiet_list = [nicks.NickPlus(i.split("#")[0], i.split("#")[1])
                          if len(i.split("#")) > 1
                          else nicks.NickPlus(i)
                          for i in bot.config.general.get_list('presence_quieters')]
        if bot.config.has_option('general', 'input_whitelist'):
            ignore_whitelist = [nicks.NickPlus(i.split("#")[0], i.split("#")[1])
                                if len(i.split("#")) > 1
                                else nicks.NickPlus(i)
                                for i in bot.config.general.get_list('input_whitelist')]
        if bot.config.has_option('general', 'presence_whitelist'):
            quiet_whitelist = [nicks.NickPlus(i.split("#")[0], i.split("#")[1])
                               if len(i.split("#")) > 1
                               else nicks.NickPlus(i)
                               for i in bot.config.general.get_list('presence_whitelist')]
    if 'general_lock' not in bot.memory:
        bot.memory['general_lock'] = threading.Lock()
    with bot.memory['general_lock']:
        if 'general' not in bot.memory:
            bot.memory['general'] = {}
        if 'ignore' not in bot.memory['general']:
            bot.memory['general']['ignore'] = ignore_list
        if 'quiet' not in bot.memory['general']:
            bot.memory['general']['quiet'] = quiet_list
        if 'ignore_whitelist' not in bot.memory['general']:
            bot.memory['general']['ignore_whitelist'] = ignore_whitelist
        if 'quiet_whitelist' not in bot.memory['general']:
            bot.memory['general']['quiet_whitelist'] = quiet_whitelist


def ignore_nick(bot, nick, hostname=None):
    '''To be referenced by other modules. provide a string, Nick, or NickPlus as the nick
    argument. Optional hostname to be provided w/ string or Nick'''
    if hostname:
        rube = nicks.NickPlus(nick, hostname)
    else:
        rube = nick
    if rube not in bot.memory['general']['ignore_whitelist'] and rube in bot.memory['general']['ignore']:
        return rube
    return None


def exists_quieting_nick(bot, channel):
    '''To be referenced by other modules'''
    for n in bot.memory['general']['quiet']:
        if nicks.in_chan(bot, channel, n):
            # This list comprehension gets list of nicks in room, filters for
            # quieted match, then filters out whitelisted. If any are left they
            # are valid quieting nicks.
            if [i for i in nicks.in_chan(bot, channel) if i == n and i not in bot.memory['general']['quiet_whitelist']]:
                return n
    return None


if __name__ == "__main__":
    print(__doc__.strip())
