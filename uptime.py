"""
uptime.py - A simple Willie module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import time
from datetime import timedelta

from willie.module import commands


def setup(Willie):
    if "uptime" not in Willie.memory:
        Willie.debug(u"uptime:startup",
                     u"Found no time, adding.",
                     u"verbose"
                     )
        Willie.memory["uptime"] = int(time.time())
    else:
        Willie.debug(u"uptime:startup",
                     u"Found time.",
                     u"verbose"
                     )


@commands('uptime')
def uptime(Willie, trigger):
    now = int(time.time())
    then = Willie.memory["uptime"]
    diff = str(timedelta(seconds=now - then))
    Willie.debug(u"uptime", diff, u"verbose")
    Willie.debug(u"uptime", len(diff), u"verbose")
    if len(diff) < 9:
        h, m, s = diff.split(":")
        d = '0 days'
    else:
        d, m, s = diff.split(":")
        d, h = d.split(", ")
    Willie.say((u"I have had %s, %s hours, %s minutes and %s " +
                u"seconds of uptime.") % (d, h, m, s)
               )


if __name__ == "__main__":
    print __doc__.strip()
