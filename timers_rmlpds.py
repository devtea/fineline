# coding=utf8
"""
timers_rmlpds.py - A simple willie module template
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import threading
import time
import random
from datetime import datetime
from urllib2 import HTTPError

import praw
import praw.errors
from praw.errors import InvalidUser, InvalidSubreddit
from requests import HTTPError

from colors import *

_UA='FineLine IRC bot 0.1 by /u/tdreyer1'
_check_interval = 3*60*60  # Seconds between checks
_channels = ['#reddit-mlpds','#fineline_testing']  # Can be no more than 2 chans

# Use multiprocess handler for multiple bots/threads on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)


def rmlpds(willie):
    """Checks the subreddit for unattended recent posts."""
    if "rmlpds_timer" not in willie.memory["timers"]:
        willie.debug('timers_rmlpds.py',
                'rmlpds_timer not found, adding',
                'verbose'
                )
        # Set the timer and do the first check in a minute
        willie.memory["timers"]["rmlpds_timer"] = time.time()-_check_interval+60
    if "rmlpds_timer_lock" not in willie.memory:
        willie.debug('timers_rmlpds.py',
                'rmlpds_timer_lock not found, adding',
                'verbose'
                )
        willie.memory["rmlpds_timer_lock"] = threading.Lock()
    if willie.memory["timers"]["rmlpds_timer"] > time.time()-_check_interval:
        return  # return if not enough time has elapsed since last full run
    willie.memory["rmlpds_timer_lock"].acquire()
    try:
        try:
            mlpds = rc.get_subreddit('MLPDrawingSchool')
        except (InvalidSubreddit, HTTPError):
            sub_exists = False
        else:
            sub_exists = True
        finally:
            # Set the timer for a 5 min. retry in case something goes wrong.
            willie.memory["timers"]["rmlpds_timer"] = time.time()-_check_interval+(5*60)
        if sub_exists:
            willie.debug('timers_rmlpds.py', "Sub exists.", "verbose")
            new_posts = mlpds.get_new(limit=50)
            uncommented = []
            for post in new_posts:
                # No comments, and between 8 and 48 hrs old
                if post.num_comments == 0 and \
                        post.created_utc > (time.time()-(48*60*60)) and \
                        post.created_utc < (time.time()-(8*60*60)):
                    willie.debug('timers_rmlpds.py', "Adding post to list.", "verbose")
                    uncommented.append(post)
            if uncommented:
                willie.debug('timers_rmlpds.py', "There are %i uncommented posts." % len(uncommented), "verbose")
                # There were posts, so set full timer
                willie.memory["timers"]["rmlpds_timer"] = time.time()
                post = random.choice(uncommented)
                c_date = datetime.utcfromtimestamp(post.created_utc)
                f_date = c_date.strftime('%b %d')
                for chan in _channels:
                    willie.msg(
                            chan,
                            "Hey everyone, there are posts that might need " +
                            "critique! Here's a random one: ")
                    nsfw = u''
                    if post.over_18:
                        nsfw =  u'[%s] ' % colorize(u'NSFW', ['red'], ['b'])
                    willie.msg(
                            chan,
                            u'%s%s posted on %s – "%s" [ %s ] ' % (
                                nsfw,
                                colorize(post.author.name, ['purple']),
                                f_date,
                                colorize(post.title, ['navy']),
                                post.short_link
                                ))
            else:
                # There were no posts, so set a short timer
                willie.memory["timers"]["rmlpds_timer"] = time.time()-(_check_interval*3/4)
                willie.debug(
                        "timers_rmlpds",
                        "No uncommented posts found.",
                        "verbose"
                        )
        else:
            willie.debug("timers_rmlpds", "Cannot check posts.", "warning")
    finally:
        willie.memory["rmlpds_timer_lock"].release()


if __name__ == "__main__":
    print __doc__.strip()
