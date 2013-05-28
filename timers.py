"""
timers.py - A simple Willie module to support timed activites
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import time
import threading

def setup(Willie):
    def daemon(Willie):
        global _on
        _on = True
        Willie.debug("Daemon", "started", "verbose")
        time.sleep(5)
        while True:
            time.sleep(5)
            while _on:
                time.sleep(5)
                timer_manager(Willie)
    # Ensure we don't spawn threads if one already exists
    if [n for n in threading.enumerate() if n.getName() == 'timer_daemon']:
        Willie.debug("Daemon", "Test found thread", "verbose")
        Willie.debug(
                "Daemon",
                "You must restart to reload the main timer thread.",
                "warning")
    else:
        Willie.debug("Daemon", "Test found no existing threads", "verbose")
        targs = (Willie,)
        t = threading.Thread(target=daemon, name='timer_daemon', args=targs)
        t.start()

def timer_manager(Willie):
    Willie.debug("Daemon", "beep", "verbose")


def timers_off(Willie, trigger):
    """Disable the slow room timer"""
    Willie.say(r'Switching daemon off.')
    global _on
    _on = False
timers_off.commands = ['sroff']
timers_off.priority = 'high'

def timers_on(Willie, trigger):
    """Enable the slow room timer"""
    Willie.say(r'Switching daemon on.')
    global _on
    _on = True
timers_on.commands = ['sron']
timers_on.priority = 'high'

def timers_status(Willie, trigger):
    """Display status of the slow room timer"""
    if _on:
        Willie.say(r'The slow room timer is running.')
    else:
        Willie.say(r'The slow room timer is not running.')
timers_status.commands = ['srstatus']
timers_status.priority = 'medium'


if __name__ == "__main__":
    print __doc__.strip()
