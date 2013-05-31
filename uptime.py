"""
uptime.py - A simple Willie module
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import time
from datetime import timedelta

def setup(Willie):
    if "uptime" not in Willie.memory:
        Willie.debug(
                "uptime:startup",
                "Found no time, adding.",
                "verbose"
                )
        Willie.memory["uptime"] = int(time.time())
    else:
        Willie.debug(
                "uptime:startup",
                "Found time.",
                "verbose"
                )


def uptime(Willie, trigger):
    now = int(time.time())
    then = Willie.memory["uptime"]
    diff = str(timedelta(seconds=now-then))
    Willie.debug("uptime", diff, "verbose")
    Willie.debug("uptime", len(diff), "verbose")
    if len(diff) < 9:
        h, m, s = diff.split(":")
        d = '0 days'
    else:
        d, m, s = diff.split(":")
        d, h = d.split(", ")
    Willie.say(("I have had %s, %s hours, %s minutes and %s " +
        "seconds of uptime.") % (d, h, m, s))
uptime.commands = ['uptime']
uptime.priority = 'low'
uptime.rate = 300


if __name__ == "__main__":
    print __doc__.strip()
