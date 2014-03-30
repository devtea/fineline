"""
uptime.py - A simple willie module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import time
from datetime import timedelta

from willie.module import commands


def setup(bot):
    if "uptime" not in bot.memory:
        bot.debug(u"uptime:startup",
                  u"Found no time, adding.",
                  u"verbose"
                  )
        bot.memory["uptime"] = int(time.time())
    else:
        bot.debug(u"uptime:startup",
                  u"Found time.",
                  u"verbose"
                  )


@commands('uptime')
def uptime(bot, trigger):
    now = int(time.time())
    then = bot.memory["uptime"]
    diff = str(timedelta(seconds=now - then))
    bot.debug(u"uptime", diff, u"verbose")
    bot.debug(u"uptime", len(diff), u"verbose")
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
    print __doc__.strip()
