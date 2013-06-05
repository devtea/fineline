# coding=utf8
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
import re
import feedparser


def setup(Willie):
    Willie.memory["timers"] = {}
    Willie.memory["timer_lock"] = threading.Lock()
    Willie.memory["fetch_rss_lock"] = threading.Lock()
    Willie.memory["timers"]["fetch_rss"] = {}
    Willie.memory["timers"]["timer_quiet_room"] = {}

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
    slow_room(Willie)


def fetch_rss(Willie, feed_url):
    '''Determines if the specified RSS feed can be loaded from an existing
    cache, or if it will need to be reloaded.

    '''
    def refresh_feed(Willie, url):
        try:
            feedparser.parse(url)
            Willie.memory["timers"]["fetch_rss"][feed_url].append(time.time())
            Willie.memory["timers"]["fetch_rss"][feed_url].append(
                    feedparser.parse(feed_url))
            Willie.debug("timers:fetch_rss", "Updated feed and stored " + \
                    "cached version.", "verbose")
        except:
            Willie.debug("timers:fetch_rss", "Could not update feed, " + \
                    "using cached version.", "verbose")
    Willie.memory["fetch_rss_lock"].acquire()
    try:
        # {feed_url: [time, feed]}
        if feed_url in Willie.memory["timers"]["fetch_rss"]:
            Willie.debug(
                    "timers:fetch_rss",
                    "Found cached RSS feed, checking age.",
                    "verbose"
                    )
            if Willie.memory["timers"]["fetch_rss"][feed_url][0] > time.time() - (60*60*10): # 10 hours
                Willie.debug(
                        "timers:fetch_rss",
                        "Feed is young, using cached version",
                        "verbose"
                        )
            else:
                refresh_feed(Willie, feed_url)
        else:  # No cached version, try to get new
            Willie.memory["timers"]["fetch_rss"][feed_url] = []
            refresh_feed(Willie, feed_url)
        return Willie.memory["timers"]["fetch_rss"][feed_url][1]
    finally:
        Willie.memory["fetch_rss_lock"].release()


def slow_room(Willie):
    """A collection of actions to perform when the room is inactive for a
    period of time.

    """
    # Wait time in seconds before the bot will pipe up
    WAIT_TIME = (random.uniform(28,47) * 60)
    Willie.debug("timers:slow_room", "beep", "verbose")

    def fzoo(Willie, channel):
        Willie.msg(channel, r"!fzoo")

    def quote(Willie, channel):
        Willie.msg(channel, r"!quote")

    def arttip(Willie, channel):
        Willie.msg(channel, r"!arttip")

    def sing(Willie, channel):
        Willie.msg(channel, random.choice([
                u"♫My little pony, my little pony!♪",
                u"♫When I was a little filly and the sun was going down...♪",
                u"♫Oh the Grand Galloping Gala is the best place for me!♪",
                u"♫It's not very far; just move your little rump!♪",
                u"♫She's an evil enchantress; She does evil dances!♪",
                u"♫Three months of winter coolness and awesome holidays!♪",
                u"♫Winter wrapup, winter wrapup!♪",
                u"♫Cupcakes! Cupcakes, cupcakes, CUPCAKES!♪",
                u"♫Thread by thread, stitching it together♪",
                u"♫Hush now, quiet now; It's time to lay your sleepy head.♪",
                u"♫What is this place, filled with so many wonders?♪",
                u"♫This is your singing telegram, I hope it finds you well!♪",
                u"♫At the Gala, at the Gala!♪",
                u"♫Can't settle for less, 'cause I'm the best♪",
                u"♫I'm the type of pony every pony, every pony should know♪",
                u"♫The fire of friendship lives in our hearts♪",
                u"♫The perfect stallion you and I must find♪",
                u"♫'Cause I love to make you smile, smile, smile♪",
                u"♫My big brother, best friend forever!♪",
                u"♫This day is going to be perfect...♪",
                u"♫Love is in bloom! A beautiful bride, a handsome groom♪",
                u"♫I was prepared to do my best...♪",
                u"♫We can save the Crystal Ponies with their history!♪",
                u"♫Babs Seed, Babs Seed, what we gonna do?♪",
                u"♫All we need to strive to be; Is part of the Apple family!♪",
                u"♫Morning in Ponyville shimmers; Morning in Ponyville shines♪",
                u"♫It's what my cutie mark is telling me♪",
                u"♫I have to find a way, to make this all okay♪",
                u"♫A True, True Friend helps a friend in need!♪",
                u"♫You've come such a long, long way...♪"
                ]))

    def poke(Willie, channel):
        Willie.msg(channel, "\001ACTION pokes the chat\001")
        if random.uniform(0,1) > 0.9:
            time.sleep(1)
            Willie.msg(channel, "It's dead Jim.")

    def cute(Willie, channel):
        da_favs = 'http://backend.deviantart.com/rss.xml' + \
                '?q=favby%3Atdreyer1%2F50127477&type=deviation'
        pics = []
        intro = [
                "It's a bit slow in here right now. How about a pony pic?",
                "I guess my owner likes this pic, but I'm not sure. " + \
                        "What do you all think?",
                "Y'all are boring. Have a pony.",
                random.choice(["Pone!", "Pony!", "Poni!"]),
                "Pony should pony pony pony",
                "[](/ppwatching-r-90)",
                "\001ACTION yawns blearily and a URL squirts out!\001"
                ]
        feed = fetch_rss(Willie, da_favs)
        if feed:
            for item in feed.entries:
                pics.append(item.link)
            Willie.msg(channel, random.choice(intro))
            time.sleep(random.uniform(1,3))
            Willie.msg(channel, random.choice(pics))
        else:
            Willie.msg(channel, "[](/derpyshock) Oh no, I was going to " + \
                    "post from DA, but something went wrong!")

    Willie.memory["timer_lock"].acquire()
    try:
        for key in Willie.memory["timers"]["timer_quiet_room"]:
            if Willie.memory["timers"]["timer_quiet_room"][key] < time.time() - WAIT_TIME:
                function = random.randint(0,8)
                if function == 0:
                    poke(Willie, key)
                elif function == 1:
                    fzoo(Willie, key)
                elif function == 2:
                    quote(Willie, key)
                elif function == 3:
                    arttip(Willie, key)
                elif function == 4:
                    sing(Willie, key)
                # This is a bad way to do probablity and you should feel bad
                elif function in range(5,8):  # It's easy, though, so fuck off
                    cute(Willie, key)
                Willie.memory["timers"]["timer_quiet_room"][key] = time.time() # update the time to now
    finally:
        Willie.memory["timer_lock"].release()


def last_activity(Willie, trigger):
    """Keeps track of the last activity for a room"""
    if trigger.sender.startswith("#") and \
            trigger.sender != "#fineline_testing":
        Willie.debug("timers:last_activity", trigger.sender, "verbose")
        Willie.memory["timer_lock"].acquire()
        try:
            Willie.memory["timers"]["timer_quiet_room"][trigger.sender] = time.time()
        finally:
            Willie.memory["timer_lock"].release()
last_activity.rule = '.*'


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
