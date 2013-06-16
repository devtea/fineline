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
import timers_rmlpds
import timers_timer

TIMER_FREQ = 1


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
                time.sleep(TIMER_FREQ)
                timer_manager(Willie)
    # Ensure we don't spawn threads if one already exists
    if [n for n in threading.enumerate() if n.getName() == 'timer_daemon']:
        Willie.debug("timers:daemon", "Test found thread", "verbose")
        Willie.debug(
                "Daemon",
                "You must restart to reload the main timer thread.",
                "warning")
    else:
        targs = (Willie,)
        t = threading.Thread(target=daemon, name='timer_daemon', args=targs)
        t.daemon = True # keep this thread from zombifying the whole program
        t.start()


def timer_manager(Willie):
    """Management function to handle threading multiple timer actions"""
    # Slow Room thread section
    def t_slow(Willie):
        timers_slow.slow_room(Willie)
    if [n for n in threading.enumerate() if n.getName() == 't_slow']:
        Willie.debug(
                "timers:timer_manager",
                "Test found thread for t_slow.",
                "verbose"
                )
    else:
        targs = (Willie,)
        thread_slow = threading.Thread(
                target=t_slow,
                name='t_slow',
                args=targs
                )
        thread_slow.daemon = True
        thread_slow.start()

    # MLPDS checker thread section
    def t_rmlpds(Willie):
        timers_rmlpds.rmlpds(Willie)
    if [n for n in threading.enumerate() if n.getName() == 't_rmlpds']:
        Willie.debug(
                "timers:timer_manager",
                "Test found thread for t_rmlpds.",
                "verbose"
                )
    else:
        targs = (Willie,)
        thread_rmlpds = threading.Thread(
                target=t_rmlpds,
                name='t_rmlpds',
                args=targs
                )
        thread_rmlpds.daemon = True
        thread_rmlpds.start()

    # Timers thread
    def t_timer(Willie):
        timers_timer.timer_check(Willie)
    if [n for n in threading.enumerate() if n.getName() == 't_timer']:
        Willie.debug(
                "timers:timer_manager",
                "Test found thread for t_timer.",
                "verbose"
                )
    else:
        targs = (Willie,)
        thread_timer= threading.Thread(
                target=t_timer,
                name='t_timer',
                args=targs
                )
        thread_timer.daemon = True
        thread_timer.start()


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
