"""
uptime.py - A simple willie module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

from datetime import timedelta
import time

from willie.module import commands

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        print("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', ['./.willie/modules/'])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()


def setup(bot):
    if "uptime" not in bot.memory:
        bot.debug(__file__, log.format(u"Found no time, adding."), u"verbose")
        bot.memory["uptime"] = int(time.time())
    else:
        bot.debug(__file__, log.format(u"Found time."), u"verbose")


@commands('uptime')
def uptime(bot, trigger):
    now = int(time.time())
    then = bot.memory["uptime"]
    diff = str(timedelta(seconds=now - then))
    bot.debug(__file__, log.format(diff), u"verbose")
    bot.debug(__file__, log.format(len(diff)), u"verbose")
    if len(diff) < 9:
        h, m, s = diff.split(":")
        d = '0 days'
    else:
        d, m, s = diff.split(":")
        d, h = d.split(", ")
    bot.say((
        u"I have had %s, %s hours, %s minutes and %s " +
        u"seconds of uptime.") % (d, h, m, s))


if __name__ == "__main__":
    print(__doc__.strip())
