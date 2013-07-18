# coding=utf8
"""
rmlpds_checker.py - A simple willie module template
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import threading
import time
import random
import re
from datetime import datetime
import imp
import sys
#from urllib2 import HTTPError

import praw
import praw.errors
from praw.errors import InvalidSubreddit
from requests import HTTPError

#from colors import *
from willie.module import interval

_UA = u'FineLine IRC bot 0.1 by /u/tdreyer1'
_check_interval = 3 * 60 * 60  # Seconds between checks
_channels = [u'#reddit-mlpds', u'#fineline_testing']

# Use multiprocess handler for multiple bots/threads on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)

# Bot framework is stupid about importing, so we need to override so that
# the colors module is always available for import.
try:
    import colors
except:
    try:
        fp, pathname, description = imp.find_module('colors',
                                                    ['./.willie/modules/']
                                                    )
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
    finally:
        if fp:
            fp.close()


def setup(willie):
    if "rmlpds_timer" not in willie.memory:
        # Set the timer and do the first check in a minute
        willie.memory["rmlpds_timer"] = time.time() - _check_interval + 60
    if "rmlpds_timer_lock" not in willie.memory:
        willie.memory["rmlpds_timer_lock"] = threading.Lock()


def filter_posts(posts):
    def is_livestream(post):
        livestreams = [
            u'livestream.com',
            u'twitch.tv',
            u'justin.tv',
            u'youtube.com',
            u'ustream.tv',
            u'nicovideo.jp'
        ]
        for s in livestreams:
            if post.url and re.findall(s, post.url):
                return True
        if post.title and re.search(u'\[stream\]', post.title, re.IGNORECASE):
            return True
        if post.is_self and post.selftext and re.search(
                ur'\b(live)?stream(ing)?\b',
                post.title,
                flags=re.IGNORECASE
        ):
            links = re.findall(
            #    ur'https?://[^\[\]\(\)\{\}\<\>,!\s]+',
                r'(?u)(%s?(?:http|https|ftp)(?:://[^\[\]\(\)\{\}\<\>,!\s]+))',
                post.selftext,
                flags=re.IGNORECASE
            )
            for link in links:
                for s in livestreams:
                    if re.findall(s, link, flags=re.IGNORECASE):
                        return True
        return False

    def is_lounge(post):
        if post.title and re.search(
            ur'\blounge\b',
            post.title,
            re.IGNORECASE
        ):
            return True
        return False

    def is_theme(post):
        if post.title and post.is_self and re.match(
            ur'weekly (drawing )?theme',
            post.title,
            flags=re.IGNORECASE
        ):
            return True
        return False

    def is_biweekly(post):
        if post.title and post.is_self and re.search(
            ur'(st|rd|nd|th) bi-weekly( drawing)? challenge',
            post.title,
            flags=re.IGNORECASE
        ):
            return True
        return False

    criticable = []
    if posts:
        for p in posts:
            if is_livestream(p) or is_lounge(p) or is_theme(p) \
                    or is_biweekly(p):
                continue
            criticable.append(p)
    return criticable


@interval(23)
def rmlpds(willie):
    """Checks the subreddit for unattended recent posts."""
    if willie.memory["rmlpds_timer"] > time.time() - _check_interval:
        return  # return if not enough time has elapsed since last full run
    willie.memory["rmlpds_timer_lock"].acquire()
    try:
        try:
            mlpds = rc.get_subreddit(u'MLPDrawingSchool')
        except (InvalidSubreddit, HTTPError):
            sub_exists = False
        else:
            sub_exists = True
        finally:
            # Set the timer for a 5 min. retry in case something goes wrong.
            willie.memory["rmlpds_timer"] = time.time() - _check_interval + \
                (5 * 60)
        if sub_exists:
            willie.debug(u'rmlpds_checker.py', u"Sub exists.", u"verbose")
            new_posts = mlpds.get_new(limit=50)
            uncommented = []
            for post in new_posts:
                # No comments, and between 8 and 48 hrs old
                if post.num_comments == 0 and \
                    post.created_utc > (time.time() - (48 * 60 * 60)) and \
                        post.created_utc < (time.time() - (8 * 60 * 60)):
                    willie.debug(
                        u'rmlpds_checker.py',
                        u"Adding post to list.",
                        u"verbose"
                    )
                    uncommented.append(post)
            uncommented = filter_posts(uncommented)
            if uncommented:
                willie.debug(
                    u'rmlpds_checker.py',
                    u"There are %i uncommented posts." % len(uncommented),
                    u"verbose"
                )
                # There were posts, so set full timer
                willie.memory["rmlpds_timer"] = time.time()
                post = random.choice(uncommented)
                c_date = datetime.utcfromtimestamp(post.created_utc)
                f_date = c_date.strftime('%b %d')
                num = u'is at least 1 post'
                if len(uncommented) > 1:
                    num = u'are at least %i posts' % len(uncommented)
                for chan in _channels:
                    if chan in willie.channels:
                        willie.msg(
                            chan,
                            (u"Hey everyone, there %s that might need " +
                                u"critique! Here's a random one: ") % num
                        )
                        nsfw = u''
                        if post.over_18:
                            nsfw = u'[%s] ' % colors.colorize(u'NSFW',
                                                              ['red'],
                                                              ['b']
                                                              )
                        willie.msg(
                            chan,
                            u'%s%s posted on %s – "%s" [ %s ] ' % (
                                nsfw,
                                colors.colorize(post.author.name, ['purple']),
                                f_date,
                                colors.colorize(post.title, ['blue']),
                                post.short_link
                            )
                        )
            else:
                # There were no posts, so set a short timer
                willie.memory["rmlpds_timer"] = time.time() - \
                    (_check_interval * 3 / 4)
                willie.debug(
                    u"rmlpds_checker",
                    u"No uncommented posts found.",
                    u"verbose"
                )
        else:
            willie.debug(u"rmlpds_checker", u"Cannot check posts.", u"warning")
    finally:
        willie.memory["rmlpds_timer_lock"].release()


if __name__ == "__main__":
    print __doc__.strip()
