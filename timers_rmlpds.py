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

_UA='FineLine IRC bot 0.1 by /u/tdreyer1'
_check_interval = 3*60*60  # Seconds between checks
_channels = ['#reddit-mlpds','#fineline_testing']  # Can be no more than 2 chans

# Use multiprocess handler for multiple bots/threads on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)

# IRC color tags
# 0  White
# 1  Black
# 2  Blue
# 3  Green
# 4  Light Red
# 5  Brown
# 6  Purple
# 7  Orange
# 8  Yellow
# 9  Light Green
# 10 Cyan
# 11 Light Cyan
# 12 Light Blue
# 13 Pink
# 14 Grey
# 15 Light Grey
# Set with '\x03' then your number
# Reset with '\x0f'
C_RESET = u'\x0f'
C_UP = u'\x0303'  # Green
C_DN = u'\x0307'  # Orange
C_NSFW = u'\x0304'  # Red
C_CNT = u'\x0302'  # Blue
C_USER = u'\x0306'  # Purple
C_CAKE = [
        u'\x0301',
        u'\x0304',
        u'\x0302',
        u'\x0303',
        u'\x0305',
        u'\x0306',
        u'\x0307',
        u'\x0313'
        ]


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
            new_posts = mlpds.get_new(limit=50)
            uncommented = []
            for post in new_posts:
                # No comments, and between 8 and 48 hrs old
                if post.num_comments == 0 and \
                        post.created_utc > (time.time()-(48*60*60)) and \
                        post.created_utc < (time.time()-(8*60*60)):
                    uncommented.append(post)
            if uncommented:
                post_count = len(uncommented)
                post = random.choice(uncommented)
                c_date = datetime.utcfromtimestamp(post.created_utc)
                f_date = c_date.strftime('%b %d')
                for chan in _channels:
                    willie.msg(
                            chan,
                            "Hey everyone, there are posts that might need " +
                            "critique! Here's a random one: ")
                    if post.over_18:
                        nsfw =  u'%s[NSFW]%s ' % (C_NSFW, C_RESET)
                    else:
                        nsfw = u''
                    willie.msg(
                            chan,
                            u'%s%s posted on %s – %s"%s"%s [ %s ] ' % (
                                nsfw, C_USER, post.author.name, C_RESET,
                                f_date, C_CNT, post.title, C_RESET,
                                post.short_link
                                )
                            )
                # There were posts, so set full timer
                willie.memory["timers"]["rmlpds_timer"] = time.time()
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
