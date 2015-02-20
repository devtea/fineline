"""
admin_tools.py - A Willie module that provides additional admin functionality
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import time

from willie.logger import get_logger
from willie.module import commands

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

LOGGER = get_logger(__name__)


def setup(bot):
    bot.memory['shush'] = False


@commands('shush', 'stfu')
def template(bot, trigger):
    """Quiets many bot functions for a while. Admin only."""
    if not trigger.admin and not trigger.owner and not trigger.isop:
        LOGGER.WARNING(log.format('%s just tried to shush me!'), trigger.nick)
        return
    bot.reply('Okay.')
    LOGGER.info(log.format(r'%s just shushed me.'), trigger.nick)
    bot.memory['shush'] = True
    time.sleep(5 * 60)
    LOGGER.info(log.format('Done being quiet.'))
    bot.memory['shush'] = False


if __name__ == "__main__":
    print(__doc__.strip())
