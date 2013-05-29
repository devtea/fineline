"""
timers.py - A simple Willie module to support timed activites
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import time
import threading
import string
import willie.web as web

def setup(Willie):
    Willie.memory["timers"] = {}
    Willie.memory["timer_lock"] = threading.Lock()
    Willie.memory["timers"]["timer_quiet_room"] = {}
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
        t.daemon = True # keep this thread from zombifying the whole program
        t.start()

def timer_manager(Willie):
    """Management function to handle threading multiple timer actions"""
    # Not doing much yet
    slow_room(Willie)

def slow_room(Willie):
    """A collection of actions to perform when the room is inactive for a
    period of time.

    """
    WAIT_TIME = (30 * 60)  # Wait time in seconds before the bot will pipe up

    def fzoo(Willie, channel):
        Willie.msg(channel, r"!fzoo")

    def poke(Willie, channel):
        Willie.msg(channel, "\001ACTION pokes the chat\001")

    Willie.debug("Daemon:slow_room", "beep", "verbose")
    Willie.memory["timer_lock"].acquire()
    try:
        for key in Willie.memory["timers"]["timer_quiet_room"]:
            if Willie.memory["timers"]["timer_quiet_room"][key] < time.time() - WAIT_TIME:
                function = random.randint(0,1)
                if function == 0:
                    poke(Willie, key)
                elif function == 1:
                    fzoo(Willie, key)
                Willie.memory["timers"]["timer_quiet_room"][key] = time.time() # update the time to now
    finally:
        Willie.memory["timer_lock"].release()

def last_activity(Willie, trigger):
    """Keeps track of the last activity for a room"""
    Willie.debug("Daemon:slow_room", trigger.sender, "verbose")
    Willie.memory["timer_lock"].acquire()
    try:
        Willie.memory["timers"]["timer_quiet_room"][trigger.sender] = time.time()
    finally:
        Willie.memory["timer_lock"].release()
last_activity.rule = '.*'

def timers_off(Willie, trigger):
    """Disable the slow room timer"""
    if trigger.owner:
        Willie.say(r'Switching the timer daemon off.')
        Willie.debug("Daemon:timer_off", "Disabling timer thread", "verbose")
        global _on
        _on = False
timers_off.commands = ['toff']
timers_off.priority = 'high'

def timers_on(Willie, trigger):
    """Enable the slow room timer"""
    if trigger.owner:
        Willie.say(r'Switching the timer daemon on.')
        Willie.debug("Daemon:timer_on", "Enabling timer thread", "verbose")
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

def timer_test(Willie, trigger):
    if trigger.owner:
        pony_mind_bleach_url = "http://old.ponymindbleach.com/"
        web.get(pony_mind_bleach_url)
timer_test.commands = ['test']

if __name__ == "__main__":
    print __doc__.strip()
