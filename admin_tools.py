"""
admin_tools.py - A Willie module that provides additional admin functionality
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import os.path
import time

from willie.logger import get_logger
from willie.module import commands

LOGGER = get_logger(__name__)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()


def setup(bot):
    bot.memory['shush'] = False


@commands(u'shush', u'stfu')
def template(bot, trigger):
    """Quiets many bot functions for a while. Admin only."""
    if not trigger.admin and not trigger.owner and not trigger.isop:
        LOGGER.WARNING(log.format('%s just tried to shush me!'), trigger.nick)
        return
    bot.reply(u'Okay.')
    LOGGER.info(log.format(r'%s just shushed me.'), trigger.nick)
    bot.memory['shush'] = True
    time.sleep(5 * 60)
    LOGGER.info(log.format('Done being quiet.'))
    bot.memory['shush'] = False


if __name__ == "__main__":
    print(__doc__.strip())
