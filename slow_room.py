"""
slow_room.py - A simple willie module to pipe up when things are slow.
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

"""
# todo add boop
import datetime
import feedparser
import random
# from socket import EBADF
import time
import threading

from willie.logger import get_logger
from willie.module import interval, rule, commands, rate, example

# Bot framework is stupid about importing, so we need to do silly stuff
try:
    import log
except:
    import sys
    import os.path
    sys.path.append(os.path.join('.', '.willie', 'modules'))
    import log
    if 'log' not in sys.modules:
        sys.modules['log'] = log

LOGGER = get_logger(__name__)
_INCLUDE = ['#reddit-mlpds']
_REFRESH_TIME = (5 * 60)  # Time between RSS refreshes


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
        for key in bot.memory["slow_timer"]:
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
            except:
                # It appears a bad file descriptor can be cached when the bot
                # disconnects and reconnects. We need to flush these.
                # del bot.memory["slow_timer"][key]
                LOGGER.error('Caught exception in slow room module.', exc_info=True)
                bot.memory["slow_timer"] = {}


def fetch_rss(bot, feed_url):
    '''Determines if the specified RSS feed can be loaded from an existing
    cache, or if it will need to be reloaded.

    '''

    def refresh_feed(bot, url):
        try:
            feedparser.parse(url)
        except:
            LOGGER.warning(log.format("Could not update feed, using cached version."))
            return
        bot.memory["fetch_rss"][feed_url] = []
        bot.memory["fetch_rss"][feed_url].append(time.time())
        bot.memory["fetch_rss"][feed_url].append(feedparser.parse(feed_url))
    with bot.memory["fetch_rss_lock"]:
        # {feed_url: [time, feed]}
        if feed_url in bot.memory["fetch_rss"]:
            if not bot.memory["fetch_rss"][feed_url][0] > time.time() - (60 * 60 * 48):  # refresh every 48 hours
                refresh_feed(bot, feed_url)
        else:  # No cached version, try to get new
            refresh_feed(bot, feed_url)
        return bot.memory["fetch_rss"][feed_url][1]


def fzoo(bot, channel):
    x = random.uniform(0, 1)
    oos = 'o' * int(50 * x ** 4 - x ** 3 - 5 * x ** 2 + 2)
    bot.msg(channel, "!fzo%s ♥" % oos)


def quote(bot, channel):
    bot.msg(channel, "!quote")
    time.sleep(random.uniform(3, 5))
    if random.uniform(0, 1) < 0.3:
        bot.msg(channel, "[](/ppfear)")


def arttip(bot, channel):
    bot.msg(channel, "!arttip")


def sing(bot, channel):
    bot.msg(channel, random.choice([
        "♫My little pony, my little pony!♪",
        "♫When I was a little filly and the sun was going down...♪",
        "♫Oh the Grand Galloping Gala is the best place for me!♪",
        "♫It's not very far; just move your little rump!♪",
        "♫She's an evil enchantress; She does evil dances!♪",
        "♫Three months of winter coolness and awesome holidays!♪",
        "♫Winter wrapup, winter wrapup!♪",
        "♫Cupcakes! Cupcakes, cupcakes, CUPCAKES!♪",
        "♫Thread by thread, stitching it together♪",
        "♫Hush now, quiet now; It's time to lay your sleepy head.♪",
        "♫What is this place, filled with so many wonders?♪",
        "♫This is your singing telegram, I hope it finds you well!♪",
        "♫At the Gala, at the Gala!♪",
        "♫Can't settle for less, 'cause I'm the best♪",
        "♫I'm the type of pony every pony, every pony should know♪",
        "♫The fire of friendship lives in our hearts♪",
        "♫The perfect stallion you and I must find♪",
        "♫'Cause I love to make you smile, smile, smile♪",
        "♫My big brother, best friend forever!♪",
        "♫This day is going to be perfect...♪",
        "♫Love is in bloom! A beautiful bride, a handsome groom♪",
        "♫I was prepared to do my best...♪",
        "♫We can save the Crystal Ponies with their history!♪",
        "♫Babs Seed, Babs Seed, what we gonna do?♪",
        "♫All we need to strive to be; Is part of the Apple family!♪",
        "♫Morning in Ponyville shimmers; Morning in Ponyville shines♪",
        "♫It's what my cutie mark is telling me♪",
        "♫I have to find a way, to make this all okay♪",
        "♫A True, True Friend helps a friend in need!♪",
        "♫You've come such a long, long way...♪",
        "♫We've got hearts as strong as horses♪",
        "♪You see one comin', you'd better run and hide!♫",
        "♫Oh, Manehattan, what you do to me♪",
        "♪We're Apples forever, Apples together; We're family, but so much more♫",
        "♫Today I planned a party, and it's just for you!♪",
        "♪For there's only one great party pony -- that is Pinkie Pie♫",
        "♫Time to make a wish, better make it right now!♪",
        "♪And the music makes your heart soar in reply♫",
        "♫When you find yo've got the music; You've got to look inside and find♪",
        "♪Know that your time is coming soon; As the sun rises, so does the moon♫",
        "♫Let the rainbow remind you; That together we will always shine♪"
    ]))


@commands('sing')
@example('!sing')
@rate('120')
def why_is_this_bot_singing(bot, trigger):
    sing(bot, trigger.sender)


def poke(bot, channel):
    bot.msg(channel, "\001ACTION pokes the chat\001")
    if random.uniform(0, 1) > 0.9:
        time.sleep(1)
        bot.msg(channel, "It's dead Jim.")


def cute(bot, channel, is_timer=True):
    pics = []
    intro = [
        "It's a bit slow in here right now. How about a pony pic?",
        "I guess my owner likes this pic, but I'm not sure. What do you all think?",
        "Y'all are boring. Have a pony.",
        random.choice(["Pone!", "Pony!", "Poni!"]),
        "Pony should pony pony pony",
        "[](/ppwatching-r-90)",
        "\001ACTION yawns blearily and a URL pops out!\001"
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
        bot.msg(channel, "[](/derpyshock) Oh no, I was going to " +
                         "post from DA, but something went wrong!")


def features(bot, channel):
    bot.msg(channel, random.choice([
        "Looking for something to do? I'd be happy to !stream an episode or five.",
        'Want to know when a stream goes live? !live subscribe!',
        'Need a Bob Ross fix? !bob',
        "Don't forget that I'm a smart pony and can do lots of neat stuff like !stream, !timer, !prompt, !queue, and more!"
    ]))


@rule('.*')
def last_activity(bot, trigger):
    """Keeps track of the last activity for a room"""
    if trigger.sender.startswith("#") and \
            trigger.sender in _INCLUDE:
        LOGGER.info(log.format(trigger.sender))
        if 'slow_timer_lock' not in bot.memory:
            LOGGER.warning(log.format('WTF Devs'))
            setup(bot)
        with bot.memory["slow_timer_lock"]:
            bot.memory["slow_timer"][trigger.sender] = time.time()


@commands('pony', 'pon[ie]')
def pony(bot, trigger):
    '''Links to a random pony pic from a curated collection of quality art.'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    LOGGER.info(log.format('Triggered'))
    LOGGER.info(log.format(trigger.sender))
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


@commands('countdown', 'cd')
def countdown(bot, trigger):
    '''Shows a countdown to a set date and time.'''
    cd(bot, trigger.sender, is_timer=False)
"""

if __name__ == "__main__":
    print(__doc__.strip())
