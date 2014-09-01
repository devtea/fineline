# coding=utf8
"""
slow_room.py - A simple willie module to pipe up when things are slow.
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

"""
# todo add boop
from __future__ import print_function

import datetime
import feedparser
import random
from socket import EBADF
import time
import threading

from willie.module import interval, rule, commands

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

# Wait time in seconds before the bot will pipe up
_INCLUDE = [u'#reddit-mlpds']
_REFRESH_TIME = (5 * 60)  # Time between RSS refreshes
# TODO move this to config file


def setup(bot):
    bot.memory['slow_wait'] = (random.uniform(23, 33) * 60)
    if "fetch_rss" not in bot.memory:
        bot.memory["fetch_rss"] = {}
    if "fetch_rss_lock" not in bot.memory:
        bot.memory["fetch_rss_lock"] = threading.Lock()
    if "slow_timer" not in bot.memory:
        bot.memory["slow_timer"] = {}
    if "slow_timer_lock" not in bot.memory:
        bot.memory["slow_timer_lock"] = threading.Lock()
    # link to deviant art RSS feed, preferably favorites.
    bot.memory["da_faves"] = bot.config.slow_room.deviant_link


@interval(19)
def slow_room(bot):
    """A collection of actions to perform when the room is inactive for a
    period of time.

    """
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    bot.memory['slow_wait'] = (random.uniform(23, 33) * 60)

    with bot.memory["slow_timer_lock"]:
        for key in bot.memory["slow_timer"].keys():
            try:
                if bot.memory["slow_timer"][key] < time.time() - bot.memory['slow_wait'] \
                        and key in bot.channels:
                    function = random.randint(0, 11)
                    if function == 0:
                        poke(bot, key)
                    elif function == 1:
                        fzoo(bot, key)
                    elif function == 2:
                        quote(bot, key)
                    elif function == 3:
                        arttip(bot, key)
                    elif function == 4:
                        sing(bot, key)
                    # This is a bad way to do probablity and you should feel bad
                    elif function in range(5, 8):  # It's easy though, so fuck off
                        cute(bot, key)
                    elif function in range(9, 11):  # No really, go away
                        features(bot, key)
                    bot.memory["slow_timer"][key] = time.time()
                else:
                    if bot.memory["slow_timer"][key] < time.time() - _REFRESH_TIME:
                        fetch_rss(bot, bot.memory["da_faves"])  # update feed regularly
            except EBADF:
                # It appears a bad file descriptor can be cached when the bot
                # disconnects and reconnects. We need to flush these.
                del bot.memory["slow_timer"][key]


def fetch_rss(bot, feed_url):
    '''Determines if the specified RSS feed can be loaded from an existing
    cache, or if it will need to be reloaded.

    '''

    def refresh_feed(bot, url):
        try:
            feedparser.parse(url)
        except:
            bot.debug(__file__, log.format(u"Could not update feed, using cached version."), u"verbose")
            return
        bot.memory["fetch_rss"][feed_url] = []
        bot.memory["fetch_rss"][feed_url].append(time.time())
        bot.memory["fetch_rss"][feed_url].append(feedparser.parse(feed_url))
        bot.debug(__file__, log.format(u"Updated feed and stored cached version."), u"verbose")
    with bot.memory["fetch_rss_lock"]:
        # {feed_url: [time, feed]}
        bot.debug(__file__, log.format('Checking feed url %s' % feed_url), 'verbose')
        if feed_url in bot.memory["fetch_rss"]:
            bot.debug(__file__, log.format(u"Found cached RSS feed, checking age."), u"verbose")
            bot.debug(__file__, log.format(bot.memory["fetch_rss"][feed_url][0]), 'verbose')
            if bot.memory["fetch_rss"][feed_url][0] > time.time() - (60 * 60 * 48):  # refresh every 48 hours
                bot.debug(__file__, log.format(u"Feed is young, using cached version"), u"verbose")
            else:
                refresh_feed(bot, feed_url)
        else:  # No cached version, try to get new
            refresh_feed(bot, feed_url)
        return bot.memory["fetch_rss"][feed_url][1]


def fzoo(bot, channel):
    x = random.uniform(0, 1)
    oos = u'o' * int(50 * x ** 4 - x ** 3 - 5 * x ** 2 + 2)
    bot.msg(channel, u"!fzo%s ♥" % oos)


def quote(bot, channel):
    bot.msg(channel, ur"!quote")
    time.sleep(random.uniform(3, 5))
    if random.uniform(0, 1) < 0.3:
        bot.msg(channel, ur"[](/ppfear)")


def arttip(bot, channel):
    bot.msg(channel, ur"!arttip")


def sing(bot, channel):
    bot.msg(channel, random.choice([
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


def poke(bot, channel):
    bot.msg(channel, u"\001ACTION pokes the chat\001")
    if random.uniform(0, 1) > 0.9:
        time.sleep(1)
        bot.msg(channel, u"It's dead Jim.")


def cute(bot, channel, is_timer=True):
    pics = []
    intro = [
        u"It's a bit slow in here right now. How about a pony pic?",
        u"I guess my owner likes this pic, but I'm not sure. What do you all think?",
        u"Y'all are boring. Have a pony.",
        random.choice([u"Pone!", u"Pony!", u"Poni!"]),
        u"Pony should pony pony pony",
        u"[](/ppwatching-r-90)",
        u"\001ACTION yawns blearily and a URL pops out!\001"
    ]
    feed = fetch_rss(bot, bot.memory["da_faves"])
    if feed:
        for item in feed.entries:
            pics.append(item.link)
        if is_timer:
            bot.msg(channel, random.choice(intro))
            time.sleep(random.uniform(1, 3))
        bot.msg(channel, random.choice(pics))
    else:
        bot.msg(channel, u"[](/derpyshock) Oh no, I was going to " +
                         u"post from DA, but something went wrong!")


def features(bot, channel):
    bot.msg(channel, random.choice([
        u"Looking for something to do? I'd be happy to !stream an episode or five.",
        u'Want to know when a stream goes live? !live subscribe!',
        u'Need a Bob Ross fix? !bob',
        u"Don't forget that I'm a smart pony and can do lots of neat stuff like !stream, !timer, !prompt, !queue, and more!"
    ]))


@rule(u'.*')
def last_activity(bot, trigger):
    """Keeps track of the last activity for a room"""
    if trigger.sender.startswith("#") and \
            trigger.sender in _INCLUDE:
        bot.debug(__file__, log.format(trigger.sender), u"verbose")
        if 'slow_timer_lock' not in bot.memory:
            bot.debug(__file__, log.format(u'WTF Devs'), u'warning')
            setup(bot)
        with bot.memory["slow_timer_lock"]:
            bot.memory["slow_timer"][trigger.sender] = time.time()


@commands(u'pony', u'pon[ie]')
def pony(bot, trigger):
    '''Returns pony pic'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    bot.debug(__file__, log.format(u'Triggered'), u'verbose')
    bot.debug(__file__, log.format(trigger.sender), u'verbose')
    cute(bot, trigger.sender, is_timer=False)


s4 = datetime.datetime(2013, 11, 23, 9)

"""
def cd(bot, channel, is_timer=True):
    diff = s4 - datetime.datetime.now()
    days = diff.days
    hrs, rem = divmod(diff.seconds, 3600)
    min, rem = divmod(rem, 60)
    parsed = ''
    if days > 0:
        parsed = '%i days' % days
    if hrs > 0:
        if days == 1:
            parsed = '%s, %i hour' % (parsed, hrs)
        elif days > 1:
            parsed = '%s, %i hours' % (parsed, hrs)
        else:
            parsed = '%i hours' % hrs
    if min > 0:
        if days > 0 or hrs > 0:
            parsed = '%s, %i minutes' % (parsed, min)
        else:
            parsed = '%i minutes' % min
    if diff.total_seconds() < 60 and diff.total_seconds() > 0:
        parsed = 'Less than a minute'
    parsed = '%s til the season 4 premier.' % parsed
    if diff.total_seconds() <= 0:
        parsed = 'SEASON 4 IS HERE!'

    bot.msg(channel, parsed)


@commands(u'countdown', u'cd')
def countdown(bot, trigger):
    '''Shows a countdown to a set date and time.'''
    cd(bot, trigger.sender, is_timer=False)
"""

if __name__ == "__main__":
    print(__doc__.strip())
