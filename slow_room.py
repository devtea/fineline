# coding=utf8
"""
slow_room.py - A simple willie module to pipe up when things are slow.
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

"""
import feedparser
import random
import time
import threading

from willie.module import interval

# Wait time in seconds before the bot will pipe up
_WAIT_TIME = (random.uniform(27, 52) * 60)
_IGNORE = [u'#fineline_testing']
_REFRESH_TIME = (5 * 60)  # Time between RSS refreshes
_da_faves = u'http://backend.deviantart.com/rss.xml' + \
            u'?q=favby%3Atdreyer1%2F50127477&type=deviation'


def setup(willie):
    if "fetch_rss" not in willie.memory:
        willie.memory["fetch_rss"] = {}
    if "fetch_rss_lock" not in willie.memory:
        willie.memory["fetch_rss_lock"] = threading.Lock()
    if "slow_timer" not in willie.memory:
        willie.memory["slow_timer"] = {}
    if "slow_timer_lock" not in willie.memory:
        willie.memory["slow_timer_lock"] = threading.Lock()


@interval(19)
def slow_room(willie):
    """A collection of actions to perform when the room is inactive for a
    period of time.

    """
    willie.memory["slow_timer_lock"].acquire()
    try:
        for key in willie.memory["slow_timer"]:
            if willie.memory["slow_timer"][key] < time.time() - _WAIT_TIME \
               and key in willie.channels:
                function = random.randint(0, 8)
                if function == 0:
                    poke(willie, key)
                elif function == 1:
                    fzoo(willie, key)
                elif function == 2:
                    quote(willie, key)
                elif function == 3:
                    arttip(willie, key)
                elif function == 4:
                    sing(willie, key)
                # This is a bad way to do probablity and you should feel bad
                elif function in range(5, 8):  # It's easy though, so fuck off
                    cute(willie, key)
                willie.memory["slow_timer"][key] = time.time()
            else:
                if willie.memory["slow_timer"][key] < time.time() - _REFRESH_TIME:
                    __ = fetch_rss(willie, _da_faves)  # update feed regularly
    finally:
        willie.memory["slow_timer_lock"].release()


def fetch_rss(willie, feed_url):
    '''Determines if the specified RSS feed can be loaded from an existing
    cache, or if it will need to be reloaded.

    '''
    def refresh_feed(willie, url):
        try:
            feedparser.parse(url)
            willie.memory["fetch_rss"][feed_url].append(time.time())
            willie.memory["fetch_rss"][feed_url].append(
                feedparser.parse(feed_url))
            willie.debug(u"timers:fetch_rss", u"Updated feed and stored " +
                         u"cached version.", u"verbose")
        except:
            willie.debug(u"timers:fetch_rss", u"Could not update feed, " +
                         u"using cached version.", u"verbose")
    willie.memory["fetch_rss_lock"].acquire()
    try:
        # {feed_url: [time, feed]}
        if feed_url in willie.memory["fetch_rss"]:
            willie.debug(
                u"timers:fetch_rss",
                u"Found cached RSS feed, checking age.",
                u"verbose"
            )
            if willie.memory["fetch_rss"][feed_url][0] > time.time() - \
               (60 * 60 * 48):  # refresh every 48 hours
                willie.debug(
                    u"timers:fetch_rss",
                    u"Feed is young, using cached version",
                    u"verbose"
                )
            else:
                refresh_feed(willie, feed_url)
        else:  # No cached version, try to get new
            willie.memory["fetch_rss"][feed_url] = []
            refresh_feed(willie, feed_url)
        return willie.memory["fetch_rss"][feed_url][1]
    finally:
        willie.memory["fetch_rss_lock"].release()


def fzoo(willie, channel):
    x = random.uniform(0, 1)
    oos = u'o' * int(50 * x ** 4 - x ** 3 - 5 * x ** 2 + 2)
    willie.msg(channel, u"!fzo%s ♥" % oos)


def quote(willie, channel):
    willie.msg(channel, ur"!quote")
    time.sleep(random.uniform(3, 5))
    willie.msg(channel, ur"[](/ppfear)")


def arttip(willie, channel):
    willie.msg(channel, ur"!arttip")


def sing(willie, channel):
    willie.msg(channel, random.choice([
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


def poke(willie, channel):
    willie.msg(channel, u"\001ACTION pokes the chat\001")
    if random.uniform(0, 1) > 0.9:
        time.sleep(1)
        willie.msg(channel, u"It's dead Jim.")


def cute(willie, channel, is_timer=True):
    pics = []
    intro = [
        u"It's a bit slow in here right now. How about a pony pic?",
        u"I guess my owner likes this pic, but I'm not sure. " +
            u"What do you all think?",
        u"Y'all are boring. Have a pony.",
        random.choice([u"Pone!", u"Pony!", u"Poni!"]),
        u"Pony should pony pony pony",
        u"[](/ppwatching-r-90)",
        u"\001ACTION yawns blearily and a URL squirts out!\001"
    ]
    feed = fetch_rss(willie, _da_faves)
    if feed:
        for item in feed.entries:
            pics.append(item.link)
        if is_timer:
            willie.msg(channel, random.choice(intro))
            time.sleep(random.uniform(1, 3))
        willie.msg(channel, random.choice(pics))
    else:
        willie.msg(channel, u"[](/derpyshock) Oh no, I was going to " +
                            u"post from DA, but something went wrong!")


def last_activity(willie, trigger):
    """Keeps track of the last activity for a room"""
    if trigger.sender.startswith("#") and \
            trigger.sender not in _IGNORE:
        willie.debug(u"timers:last_activity", trigger.sender, u"verbose")
        if 'slow_timer_lock' not in willie.memory:
            willie.debug(
                u'timers_slow:last_activity',
                u'WTF Devs',
                u'warning'
            )
            setup(willie)
        willie.memory["slow_timer_lock"].acquire()
        try:
            willie.memory["slow_timer"][trigger.sender] = time.time()
        finally:
            willie.memory["slow_timer_lock"].release()
last_activity.rule = '.*'
last_activity.priority = 'low'


if __name__ == "__main__":
    print __doc__.strip()