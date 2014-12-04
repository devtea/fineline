# coding=utf8
"""
rmlpds_checker.py - A simple willie module template
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

from datetime import datetime
import HTMLParser
import os.path
import random
import re
from socket import timeout
import threading
import time

import praw
import praw.errors
from praw.errors import InvalidSubreddit
from requests import HTTPError

from willie.module import interval, commands, rate, example

_UA = u'FineLine IRC bot 0.1 by /u/tdreyer1'
_check_interval = 3 * 60 * 60  # Seconds between checks
_channels = [u'#reddit-mlpds', u'#fineline_testing']
_INCLUDE = ['#reddit-mlpds', '#fineline_testing', '#reddit-mlpds-bots']
_bad_reddit_msg = u"That doesn't seem to exist on reddit."
_bad_user_msg = u"That user doesn't seem to exist."
_error_msg = u"That doesn't exist, or reddit is being squirrely."
_timeout_message = u'Sorry, reddit is unavailable right now.'
_util_html = HTMLParser.HTMLParser()
# Bots to be ignored go here
_excluded_commenters = []
SUB_LIMIT = 50

# Use multiprocess handler for multiple bots/threads on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        print("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()

try:
    import colors
except:
    import imp
    import sys
    try:
        print("Trying manual import of colors.")
        fp, pathname, description = imp.find_module('colors', [os.path.join('.', '.willie', 'modules')])
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
    finally:
        if fp:
            fp.close()
try:
    import util
except:
    import imp
    try:
        print("trying manual import of util")
        fp, pathname, description = imp.find_module('util', [os.path.join('.', '.willie', 'modules')])
        util = imp.load_source('util', pathname, fp)
        sys.modules['util'] = util
    finally:
        if fp:
            fp.close()


def setup(bot):
    if "rmlpds" not in bot.memory:
        bot.memory["rmlpds"] = {}
    if "rmlpds_timer" not in bot.memory["rmlpds"]:
        # Set the timer and do the first check in a minute
        bot.memory["rmlpds"]["timer"] = time.time() - _check_interval + 60
    if "rmlpds_timer_lock" not in bot.memory["rmlpds"]:
        bot.memory["rmlpds"]["lock"] = threading.Lock()

    bot.memory["rmlpds"]["vote_id"] = None
    bot.memory["rmlpds"]["vote_count"] = 0
    if "last" not in bot.memory["rmlpds"]:
        bot.memory["rmlpds"]["last"] = None

    if "exclude" not in bot.memory["rmlpds"]:
        with bot.memory['rmlpds']['lock']:
            bot.memory["rmlpds"]["exclude"] = []

            dbcon = bot.db.connect()  # sqlite3 connection
            cur = dbcon.cursor()
            try:
                # if our tables don't exist, create them
                cur.execute('''CREATE TABLE IF NOT EXISTS rmlpds
                            (id TEXT)''')
                dbcon.commit()

                cur.execute('SELECT id FROM rmlpds')
                dbload = cur.fetchall()
            finally:
                cur.close()
                dbcon.close()
            if dbload:
                bot.memory['rmlpds']['exclude'].extend(dbload)


def filter_posts(bot, posts):
    def is_livestream(post):
        livestreams = [
            u'livestream.com',
            u'twitch.tv',
            u'justin.tv',
            u'youtube.com',
            u'ustream.tv',
            u'picarto.tv',
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
                # ur'https?://[^\[\]\(\)\{\}\<\>,!\s]+',
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
        if post.title and re.search(ur'\blounge\b', post.title, re.I):
            return True
        return False

    def is_theme(post):
        if post.title and post.is_self and re.match(ur'weekly (drawing )?theme', post.title, flags=re.I):
            return True
        return False

    def is_biweekly(post):
        if post.title and post.is_self and re.search(ur'(st|rd|nd|th) bi-weekly( drawing)? challenge', post.title, flags=re.I):
            return True
        return False

    def is_train(post):
        if post.title and post.is_self and re.search(ur'\bsketch train\b', post.title, flags=re.I):
            return True
        return False

    def is_ignored(post):
        return post.id in bot.memory['rmlpds']['exclude']

    def is_excludable(post):
        if is_livestream(post):
            return True
        if is_lounge(post):
            return True
        if is_theme(post):
            return True
        if is_biweekly(post):
            return True
        if is_train(post):
            return True
        if is_ignored(post):
            return True
        return False

    criticable = []
    if posts:
        for p in posts:
            if is_excludable(p):
                continue
            criticable.append(p)
    return criticable


def filter_comments(post, limit):
    '''Returns squishy number of 'good' comments'''
    def auth_comp(comment, post):
        try:
            return i.author != post.author
        except AttributeError:
            return False

    if post.num_comments < limit:
        return post.num_comments
    # Grab flattened list of comments and remove author's posts
    flat_comments = [i for i in praw.helpers.flatten_tree(post.comments) if auth_comp(i, post)]

    if len(flat_comments) < limit:
        return len(flat_comments)
    # Filter excluded commenters like bots
    if _excluded_commenters:
        flat_comments = [i for i in flat_comments if i.author.name.lower() not in _excluded_commenters]
        if len(flat_comments) < limit:
            return len(flat_comments)
    # Filter comments that are too short and probably not good critique.
    flat_comments = [i for i in flat_comments if len(i.body) > 200]
    return len(flat_comments)


@interval(23)
def rmlpds(bot):
    """Checks the subreddit for unattended recent posts."""
    if bot.memory["rmlpds"]["timer"] > time.time() - _check_interval:
        return  # return if not enough time has elapsed since last full run
    with bot.memory["rmlpds"]["lock"]:
        try:
            mlpds = rc.get_subreddit(u'MLPDrawingSchool')
        except (InvalidSubreddit, HTTPError):
            sub_exists = False
        else:
            sub_exists = True
        finally:
            # Set the timer for a 5 min. retry in case something goes wrong.
            bot.memory["rmlpds"]["timer"] = time.time() - _check_interval + \
                (5 * 60)
        if sub_exists:
            bot.debug(__file__, log.format(u"Sub exists."), u"verbose")
            new_posts = mlpds.get_new(limit=SUB_LIMIT)
            uncommented = []
            for post in new_posts:
                # Filter old posts
                if post.created_utc < (time.time() - (48 * 60 * 60)):
                    continue
                # Filter new posts
                if post.created_utc > (time.time() - (8 * 60 * 60)):
                    continue
                if filter_comments(post, 0) > 0:
                    continue
                # bot.debug(__file__, log.format(u"Adding post to list."), u"verbose")
                uncommented.append(post)
            uncommented = filter_posts(bot, uncommented)
            if uncommented:
                bot.debug(__file__, log.format(u"There are %i uncommented posts." % len(uncommented)), u"verbose")
                # There were posts, so set full timer
                bot.memory["rmlpds"]["timer"] = time.time()
                post = random.choice(uncommented)
                bot.memory["rmlpds"]["last"] = post.id  # record last id for ignoring
                c_date = datetime.utcfromtimestamp(post.created_utc)
                td = datetime.utcnow() - c_date
                hr = td.total_seconds() / 60 / 60
                t = u'%i hours ago' % hr
                msg = u'Hey everyone, there is at least 1 post that might ' + \
                      u'need critique! Use !queue to see them all.'
                if len(uncommented) > 1:
                    msg = u'Hey everyone, there are at least %i ' % len(uncommented) + \
                          u'posts that might need critique! Use !queue to see them all, but here is a random one:'
                for chan in _channels:
                    if chan in bot.channels:
                        nsfw = u''
                        if post.over_18:
                            nsfw = u'[%s] ' % colors.colorize(u'NSFW', ['red'], ['b'])
                        bot.msg(chan, msg)
                        bot.msg(
                            chan,
                            u'%s%s posted %s – "%s" [ %s ] ' % (
                                nsfw,
                                colors.colorize(post.author.name, ['purple']),
                                t,
                                colors.colorize(_util_html.unescape(post.title), ['green']),
                                post.short_link
                            )
                        )
            else:
                # There were no posts, so set a short timer
                bot.memory["rmlpds"]["last"] = None  # clear the last post so no inadvertant ignoring takes place
                bot.memory["rmlpds"]["timer"] = time.time() - \
                    (_check_interval * 3 / 4)
                bot.debug(__file__, log.format(u"No uncommented posts found."), u"verbose")
        else:
            bot.debug(__file__, log.format(u"Cannot check posts."), u"warning")


@commands(u'queue', u'check', u'posts', u'que', u'crit', u'critique')
@rate(120)
def mlpds_check(bot, trigger):
    '''Checks for posts within the last 48h with fewer than 2 appropriate comments. Filters short comments and comments made by OP.'''
    if trigger.sender not in _INCLUDE:
        return
    bot.reply("Okay, let me look. This may take a couple minutes.")
    try:
        mlpds = rc.get_subreddit(u'MLPDrawingSchool')
    except InvalidSubreddit:
        bot.say(_bad_reddit_msg)
        return
    except HTTPError:
        bot.say(_error_msg)
        return
    except timeout:
        bot.say(_timeout_message)
        return
    new_posts = mlpds.get_new(limit=SUB_LIMIT)
    new_posts = filter_posts(bot, list(new_posts))
    uncommented = []
    for post in new_posts:
        # Filter old posts
        if post.created_utc < (time.time() - (48 * 60 * 60)):
            continue
        # Filter posts with many comments
        if post.num_comments >= 8:
            continue
        # Filter posts with more than 2 good comments
        if filter_comments(post, 2) >= 2:  # If we have at least 2 good comments...
            continue
        bot.debug(__file__, log.format('appending %s to uncommented' % post.title), 'verbose')
        uncommented.append(post)
    if uncommented:
        uncommented.reverse()  # Reverse so list is old to new
        post_count = len(uncommented)
        spammy = False
        if post_count > 4:
            spammy = True
        if spammy:
            bot.reply(u"There are a few, I'll send them in pm.")
        for post in uncommented:
            if post.num_comments == 0:
                num_com = u"There are no comments"
            elif post.num_comments == 1:
                num_com = u"There is only 1 comment"
            else:
                num_com = u"There are %i comments" % post.num_comments
            if post.author.name.lower()[len(post.author.name) - 1] == u's':
                apos = u"'"
            else:
                apos = u"'s"
            c_date = datetime.utcfromtimestamp(post.created_utc)
            f_date = c_date.strftime(u'%b %d')
            if spammy:
                bot.msg(
                    trigger.nick,
                    u'%s on %s%s post (%s) on %s entitled "%s"' % (
                        num_com,
                        colors.colorize(post.author.name, [u'purple']),
                        apos,
                        post.short_link,
                        f_date,
                        colors.colorize(_util_html.unescape(post.title), [u'green'])
                    )
                )
            else:
                bot.reply(
                    u'%s on %s%s post (%s) on %s entitled "%s"' % (
                        num_com,
                        colors.colorize(post.author.name, [u'purple']),
                        apos,
                        post.short_link,
                        f_date,
                        colors.colorize(_util_html.unescape(post.title), [u'green'])
                    )
                )
    else:
        bot.reply(u"I don't see any lonely posts. There could still be "
                  u"posts that need critiquing, though: "
                  u"http://mlpdrawingschool.reddit.com/"
                  )

re_id = re.compile(r"(https?://)?(www\.|pay\.)?reddit.com/r/MLPdrawingschool/comments/([A-Za-z0-9]{4,10})/?")
re_id2 = re.compile(r"(https?://)?redd.it/([A-Za-z0-9]{4,10})/?")
_IGNORE_VOTES = 3


@example("!ignore http://redd.it/b42k29")
@commands("ignore")
def ignore(bot, trigger):
    """Used to ignore /r/mlpdrawingschool posts that don't need attention. Either provide a
       single reddit url or nothing to ignore the last announced post."""
    def add_post(id):
        bot.memory["rmlpds"]["exclude"].append(id)
        remove = None
        if len(bot.memory["rmlpds"]["exclude"]) > 50:
            remove = bot.memory["rmlpds"]["exclude"].pop(0)

        dbcon = bot.db.connect()  # sqlite3 connection
        cur = dbcon.cursor()
        try:
            cur.execute('INSERT INTO rmlpds (id) VALUES (?)', (id,))
            if remove:
                cur.execute("DELETE FROM rmlpds WHERE id = '?'", remove)
            dbcon.commit()
        finally:
            cur.close()
            dbcon.close()

    # Don't allow PMs
    if not trigger.sender.startswith('#'):
        return
    # Ignore certain nicks
    if util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    with bot.memory["rmlpds"]["lock"]:
        target = None
        try:
            # Grab the provided URL to ignore
            target = trigger.args[1].split()[1]
        except IndexError:
            # Grab the last announced post and ignore it
            if bot.memory["rmlpds"]["last"]:
                post_id = unicode(bot.memory["rmlpds"]["last"])
            else:
                bot.reply("Sorry, nothing has been announced recently.")
                return
        if target:
            try:
                post_id = re_id.search(target).groups()[-1]  # reddit links
            except:
                try:
                    post_id = re_id2.search(target).groups()[-1]  # redd.it links
                except:
                    bot.reply("Sorry, that doesn't look like a valid post.")
                    return
        if post_id in bot.memory["rmlpds"]["exclude"]:
            bot.reply("That post is already being ignored.")
            return

    if bot.memory["rmlpds"]["vote_id"]:
        # A vote is in progress
        with bot.memory["rmlpds"]["lock"]:
            if not bot.memory["rmlpds"]["vote_id"]:  # race condition fuckup
                return
            if post_id == bot.memory["rmlpds"]["vote_id"]:
                # Vote is same, process
                if bot.memory["rmlpds"]["vote_count"] == _IGNORE_VOTES - 1:
                    bot.say("Vote succeeded. Post ignored.")
                    bot.memory["rmlpds"]["vote_id"] = None
                    bot.memory["rmlpds"]["vote_count"] = 0
                    add_post(post_id)
                else:
                    bot.memory["rmlpds"]["vote_count"] += 1
                    bot.say('%i votes of %i needed to ignore.' % (bot.memory["rmlpds"]["vote_count"], _IGNORE_VOTES))
            else:
                bot.reply("Sorry, currently voting on http://www.reddit.com/r/MLPdrawingschool/comments/%s/" % bot.memory["rmlpds"]["vote_id"])
    else:
        # New vote
        with bot.memory["rmlpds"]["lock"]:
            if bot.memory["rmlpds"]["vote_id"]:  # race condition fuckup
                return
            bot.memory["rmlpds"]["vote_id"] = unicode(post_id)
            bot.memory["rmlpds"]["vote_count"] += 1
            bot.say("Ignore vote started for http://www.reddit.com/r/MLPdrawingschool/comments/%s/" % bot.memory["rmlpds"]["vote_id"])
            bot.say("%i more votes in the next five minutes are required." % (_IGNORE_VOTES - 1))
        time.sleep(300)
        with bot.memory["rmlpds"]["lock"]:
            if bot.memory["rmlpds"]["vote_id"] == post_id:
                bot.say("Ignore vote failed.")
                bot.memory["rmlpds"]["vote_id"] = None
                bot.memory["rmlpds"]["vote_count"] = 0


if __name__ == "__main__":
    print(__doc__.strip())
