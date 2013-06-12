# coding=utf8
"""
timers.py - A simple Willie module to support timed activites
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

"""
import time
import threading
#import string

import timers_slow


def setup(Willie):
    Willie.memory["timers"] = {}

    def daemon(Willie):
        global _on
        _on = True
        Willie.debug("timers:daemon", "started", "verbose")
        time.sleep(5)
        while True:
            time.sleep(5)
            while _on:
                time.sleep(5)
                timer_manager(Willie)
    # Ensure we don't spawn threads if one already exists
    if [n for n in threading.enumerate() if n.getName() == 'timer_daemon']:
        Willie.debug("timers:daemon", "Test found thread", "verbose")
        Willie.debug(
                "Daemon",
                "You must restart to reload the main timer thread.",
                "warning")
    else:
        Willie.debug("timers:daemon", "Test found no existing threads", "verbose")
        targs = (Willie,)
        t = threading.Thread(target=daemon, name='timer_daemon', args=targs)
        t.daemon = True # keep this thread from zombifying the whole program
        t.start()


def timer_manager(Willie):
    """Management function to handle threading multiple timer actions"""
    # Not doing much yet
    timers_slow.slow_room(Willie)


def timers_off(Willie, trigger):
    """ADMIN: Disable the slow room timer"""
    if trigger.owner:
        Willie.say(r'Switching the timer daemon off.')
        Willie.debug("timers:timer_off", "Disabling timer thread", "verbose")
        global _on
        _on = False
timers_off.commands = ['toff']
timers_off.priority = 'high'


def timers_on(Willie, trigger):
    """ADMIN: Enable the slow room timer"""
    if trigger.owner:
        Willie.say(r'Switching the timer daemon on.')
        Willie.debug("timers:timer_on", "Enabling timer thread", "verbose")
        global _on
        _on = True
timers_on.commands = ['ton']
timers_on.priority = 'high'


def timers_status(Willie, trigger):
    """ADMIN: Display status of the slow room timer"""
    if trigger.owner:
        if _on:
            Willie.say(r'The timer daemon is running.')
        else:
            Willie.say(r'The timer daemon is not running.')
timers_status.commands = ['tstatus']
timers_status.priority = 'medium'


if __name__ == "__main__":
    print __doc__.strip()
