# coding=utf8
"""
rmlpds_checker.py - A simple willie module template
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import datetime
import HTMLParser
import random
import re
from socket import timeout
import threading
import time
from string import Template

import praw
import praw.errors
from praw.errors import InvalidSubreddit
from requests import HTTPError

from willie.logger import get_logger
from willie.module import interval, commands, rate, example

LOGGER = get_logger(__name__)

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
_RETRYS = 3

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
    import os.path
    try:
        LOGGER.info("Trying manual import of log formatter.")
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
    import os.path
    try:
        LOGGER.info(log.format("Trying manual import of colors."))
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
    import sys
    import os.path
    try:
        LOGGER.info(log.format("trying manual import of util"))
        fp, pathname, description = imp.find_module('util', [os.path.join('.', '.willie', 'modules')])
        util = imp.load_source('util', pathname, fp)
        sys.modules['util'] = util
    finally:
        if fp:
            fp.close()


def setup(bot):
    if "rmlpds" not in bot.memory:
        bot.memory["rmlpds"] = {}
    if "timer" not in bot.memory["rmlpds"]:
        # Set the timer and do the first check in a minute
        bot.memory["rmlpds"]["timer"] = time.time() - _check_interval + 60
    if "lock" not in bot.memory["rmlpds"]:
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
                cur.execute('''CREATE TABLE IF NOT EXISTS stor
                               (module TEXT NOT NULL,
                                item TEXT NOT NULL,
                                value TEXT,
                                    PRIMARY KEY (module, item))''')
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


def filter_posts(bot, posts, ignore=True):
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
        if ignore and is_ignored(post):
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
            LOGGER.info(log.format(u"Sub exists."))
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
                # LOGGER.info(log.format(u"Adding post to list."))
                uncommented.append(post)
            uncommented = filter_posts(bot, uncommented)
            if uncommented:
                LOGGER.info(log.format(u"There are %i uncommented posts."), len(uncommented))
                # There were posts, so set full timer
                bot.memory["rmlpds"]["timer"] = time.time()
                post = random.choice(uncommented)
                bot.memory["rmlpds"]["last"] = post.id  # record last id for ignoring
                c_date = datetime.datetime.utcfromtimestamp(post.created_utc)
                td = datetime.datetime.utcnow() - c_date
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
                LOGGER.info(log.format(u"No uncommented posts found."))
        else:
            LOGGER.warning(log.format(u"Cannot check posts."))


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
        LOGGER.info(log.format('appending %s to uncommented'), post.title)
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
            c_date = datetime.datetime.utcfromtimestamp(post.created_utc)
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


@commands('reddit_contest')
def reddit_contest(bot, trigger):
    '''Admin: Runs a comment summary for the last month. Add the 'force' argument if you want to force a refresh of data from reddit.'''
    def include_comment(reddit, comment):
        # Returns true iff comment is top level, or author has no other
        # comments higher in the thread
        this_comment = comment
        if not this_comment.author:  # Comment was deleted
            return False
        if this_comment.is_root:
            return True
        while not this_comment.is_root:
            try:
                this_comment = reddit.get_info(thing_id=this_comment.parent_id)
            except timeout:
                return True  # Reddit timed out, we'll go ahead and count the comment
            if this_comment.author and this_comment.author.name == comment.author.name:
                return False  # Comment Author has another comment higher in the thread
        return True

    def get_name(thinger):
        try:
            if thinger.name:
                return thinger.name
            else:
                raise Exception("hello sucky code")
        except:
            return '[deleted]'

    def trim_comment(text):
        try:
            words = text.split()
            if len(words) > 65:
                short = words[:65]
                short.append('...')
                return u' '.join(short)
            else:
                return text
        except:
            return u'[Processing error]'

    markup_link = re.compile(r'\[(\s*[^\]]+\s*)\]\(([^\]/][^\)]*)\)')

    if not trigger.admin:
        return

    try:
        arguments = trigger.args[1].split()[1:]
    except IndexError:
        # Nothing provided
        pass
    else:
        if arguments and (len(arguments) > 1 or arguments[0] not in ('force')):
            bot.reply("malformed arguments")
            return

    if bot.config.has_section('general') and bot.config.has_option('general', 'hosted_path') and \
            bot.config.has_option('general', 'hosted_domain'):
        tail = 'reddit_contest.html'
        bot.memory['rmlpds']['export_location'] = u'%s%s' % (bot.config.general.hosted_path, tail)
        bot.memory['rmlpds']['export_url'] = u'%s%s' % (bot.config.general.hosted_domain, tail)
    else:
        bot.reply("This module is not configured properly. Please configure the hosted path and domain in the config file.")
        return

    with bot.memory['rmlpds']['lock']:
        mlpds = rc.get_subreddit(u'MLPDrawingSchool')
        now = time.time()

        # Caching
        if (not arguments or not arguments[0] == 'force') and 'fetch_time' in bot.memory['rmlpds'] and \
                bot.memory['rmlpds']['fetch_time'][0] > time.time() - (7 * 24 * 60 * 60):
            # Load cached comments
            LOGGER.info(log.format(u"using cached comments"))
            bot.reply("Okay, I checked recently so I will use what I found then. Use 'force' if you think I need to check again.")
            now = bot.memory['rmlpds']['fetch_time'][0]
            comments = bot.memory['rmlpds']['fetch_time'][1]
            all_comments = bot.memory['rmlpds']['fetch_time'][2]
            filtered_comments = []
        else:
            LOGGER.info(log.format(u"Grabbing last 1000 comments"))
            bot.reply("Okay, this is a slow process (reddit api is slooooow) and can take up to an hour if reddit isn't behaving. I will message you with the results.")

            successful = None
            trials = 0
            while not successful and trials < _RETRYS:
                try:
                    comments = [i for i in mlpds.get_comments(limit=1000)]
                    successful = True
                except:
                    LOGGER.error(log.format(u"Exception when grabbing list of comments"), exec_info=True)
                    time.sleep(5)
                    trials += 1
            filtered_comments = []

            # Filter deleted comments
            LOGGER.info(log.format(u"Filtering deleted comments"))
            for comment in comments:
                successful = None
                trials = 0
                while not successful and trials < _RETRYS:
                    try:
                        if comment.author:
                            successful = True
                            filtered_comments.append(comment)
                    except:
                        LOGGER.error(log.format(u"Exception when filtering for deleted comment %s"), comment.id, exec_info=True)
                        time.sleep(5)
                        trials += 1
            comments = []
            comments.extend(filtered_comments)
            filtered_comments = []

            # Filter by date to include only comments made last month
            LOGGER.info(log.format(u"Filtering by date"))
            last_month = datetime.datetime.utcnow().month - 1
            if last_month == 0:
                last_month = 12
            for comment in comments:
                successful = None
                trials = 0
                while not successful and trials < _RETRYS:
                    try:
                        if datetime.datetime.utcfromtimestamp(comment.created_utc).month == last_month:
                            successful = True
                            filtered_comments.append(comment)
                    except:
                        LOGGER.error(log.format(u"Exception when filtering by date %s"), comment.id, exec_info=True)
                        time.sleep(5)
                        trials += 1
            comments = []
            comments.extend(filtered_comments)
            filtered_comments = []

            # filter by submission to exclude commonly excluded posts
            LOGGER.info(log.format(u"Filtering by submission"))
            for comment in comments:
                LOGGER.info(log.format(u"checking %s"), comment.id)
                successful = None
                trials = 0
                while not successful and trials < _RETRYS:
                    try:
                        include = filter_posts(bot, [comment.submission], ignore=False)
                        if include:
                            successful = True
                            filtered_comments.append(comment)
                    except:
                        LOGGER.error(log.format(u"Exception when filtering by submission %s"), comment.id, exec_info=True)
                        time.sleep(5)
                        trials += 1
            comments = []
            comments.extend(filtered_comments)
            filtered_comments = []

            # Filter comment if submission date more than 10 days prior to
            # comment date
            LOGGER.info(log.format(u"Filtering on time difference between post and comment"))
            for comment in comments:
                successful = None
                trials = 0
                while not successful and trials < _RETRYS:
                    try:
                        if comment.created_utc - comment.submission.created_utc < 10 * 24 * 60 * 60:  # 10 day diff
                            successful = True
                            filtered_comments.append(comment)
                    except:
                        LOGGER.error(log.format(u"Exception when filtering on time diff %s"), comment.id, exec_info=True)
                        time.sleep(5)
                        trials += 1
            comments = []
            comments.extend(filtered_comments)
            filtered_comments = []

            # Filter self comments on posts
            LOGGER.info(log.format(u"Filtering self replies"))
            for comment in comments:
                successful = None
                trials = 0
                while not successful and trials < _RETRYS:
                    try:
                        commenter = comment.author.name
                        try:
                            poster = comment.submission.author.name
                        except AttributeError:
                            poster = None  # Submission was probably deleted, we can safely assume self replies probably were too...
                        if commenter != poster:
                            successful = True
                            filtered_comments.append(comment)
                    except:
                        LOGGER.error(log.format(u"Exception when filtering self replies %s"), comment.id, exec_info=True)
                        time.sleep(5)
                        trials += 1
            comments = []
            comments.extend(filtered_comments)
            filtered_comments = []

            # Now that we've filtered using universal stuffs, make a copy of the list
            # for potential later use and apply our more strict filters
            all_comments = []
            all_comments.extend(comments)

            # filter by comment length or inclusion of link
            LOGGER.info(log.format(u"Filtering by length OR link"))
            for comment in comments:
                successful = None
                trials = 0
                while not successful and trials < _RETRYS:
                    try:
                        if len(comment.body.split()) > 100 or markup_link.search(comment.body):
                            successful = True
                            filtered_comments.append(comment)
                    except:
                        LOGGER.error(log.format(u"Exception when filtering by length or link %s"), comment.id, exec_info=True)
                        time.sleep(5)
                        trials += 1
            comments = []
            comments.extend(filtered_comments)
            filtered_comments = []

            # Only keep top level or first reply comments
            LOGGER.info(log.format(u"Filtering based on top comment and thread participation"))
            for comment in comments:
                successful = None
                trials = 0
                while not successful and trials < _RETRYS:
                    try:
                        if include_comment(rc, comment):
                            successful = True
                            filtered_comments.append(comment)
                    except:
                        LOGGER.error(log.format(u"Exception when filtering by top comment and thread participation %s"), comment.id, exec_info=True)
                        time.sleep(5)
                        trials += 1
            comments = []
            comments.extend(filtered_comments)
            filtered_comments = []

            # Save cache
            bot.memory['rmlpds']['fetch_time'] = (now, comments, all_comments)

        # Build list by commenter
        LOGGER.info(log.format(u"Building list"))
        commenters = {}
        for comment in comments:
            if comment.author.name not in commenters:
                commenters[comment.author.name] = []
            commenters[comment.author.name].append(comment)

        # Filter commenters who have fewer than 3 applicable comments
        LOGGER.info(log.format(u"Filtering less than three"))
        for commenter in commenters.keys():
            if len(commenters[commenter]) < 3:
                del commenters[commenter]

        sorted_commenters = sorted(commenters.items(), key=lambda x: len(x[1]), reverse=True)

        # Ugly code~
        t_page = Template(
            '''
            <!DOCTYPE html>
            <html>
            <h2>${month} comment report</h2>
            <p>Data collected: ${cdate} UTC <br />
            Page generated: ${gdate} UTC</p>
            ${body}
            </html>
            ''')
        t_user_section = Template(
            '''
            <p><a href="https://reddit.com/user/${user}/comments/">${userr}</a> - Filtered comments: <b>${count}</b> <br />
                <ul>
                ${comments}
                </ul>
            </p>
            ''')
        t_comment = Template(
            '''
            <li><a href="${link}">Comment</a> (${cdate} UTC) on <a href="${sub}">${title}</a> by <em>${name}</em> (${sdate} UTC)
            <br />${comment}</li>
            ''')
        t_com_link = Template('''https://reddit.com/r/${subreddit}/comments/${sid}/x/${cid}?context=10''')
        t_sub_link = Template('''https://reddit.com/r/${subreddit}/comments/${sid}/''')

        page_content = u''
        for user in sorted_commenters:  # Remember, here 'user' is a tuple
            buf = ''
            for comment in commenters[user[0]]:
                buf = '%s%s' % (buf, t_comment.substitute(
                    link=t_com_link.substitute(
                        subreddit=comment.subreddit,
                        sid=comment.submission.id,
                        cid=comment.id),
                    comment=trim_comment(_util_html.unescape(comment.body)),
                    title=_util_html.unescape(comment.submission.title),
                    cdate=str(datetime.datetime.utcfromtimestamp(comment.created_utc)),
                    sdate=str(datetime.datetime.utcfromtimestamp(comment.submission.created_utc)),
                    name=get_name(comment.submission.author),
                    sub=t_sub_link.substitute(
                        subreddit=comment.subreddit,
                        sid=comment.submission.id)))
            page_content = '%s%s' % (page_content, t_user_section.substitute(
                user=user[0],
                userr=user[0],
                count=len(user[1]),
                comments=buf))

        # Figure out last month for header
        day = datetime.datetime.utcfromtimestamp(now)
        first = datetime.date(day=1, month=day.month, year=day.year)
        last_month = first - datetime.timedelta(days=1)

        # Jam everything into the page template
        page_content = t_page.substitute(
            month=last_month.strftime('%B'),
            gdate=str(datetime.datetime.utcnow()),  # Generated time
            cdate=str(datetime.datetime.utcfromtimestamp(now)),  # Data collection time
            body=page_content)

        # Illgotten attempt at prettifying
        # from lxml import etree, html
        # page_content = etree.tostring(html.fromstring(page_content), encoding='unicode', pretty_print=True)

        # replace markdown links with html links - shouldn't be an issue to run
        # this over the whole html page, but if it is move it up to work on
        # each comment individually
        page_content = re.subn(markup_link, r'<a href="\2">\1</a>', page_content)[0]

        try:
            with open(bot.memory['rmlpds']['export_location'], 'w') as f:
                f.write(page_content.encode('utf-8', 'replace'))
        except IOError:
            LOGGER.error(log.format('IO error writing contest file. check file permissions.'), exec_info=True)
            return
        time.sleep(5)  # wait a bit for file syncing and shit so the new page is available
        LOGGER.info(log.format('Finished processing list.'))
        bot.msg(trigger.nick, 'The summary is out at %s' % bot.memory['rmlpds']['export_url'])
        bot.reply("Check your messages.")


if __name__ == "__main__":
    print(__doc__.strip())
