# coding=utf8
"""
reddit.py - A simple Willie module that provides reddit functionality
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

Depends on PRAW: https://github.com/praw-dev/praw
"""
# TODO Filter multiple posts from a single user (ie. one user posts 10x in 10 min)
# TODO add recency filter for announced reddit posts
from __future__ import print_function

from datetime import datetime
import HTMLParser
import os.path
import re
import sys
from socket import timeout
import threading
import time
import traceback

import praw
import praw.errors
from praw.errors import InvalidUser, InvalidSubreddit
from requests import HTTPError

from willie.module import commands, rule, interval, example

_url = u'(reddit\.com|redd\.it)'
_reurl = re.compile(_url, flags=re.I)
_partial = ur'((^|[^A-Za-z0-9])/(r|u(ser)?)/[^/\s\.]{3,20})'
_util_html = HTMLParser.HTMLParser()
_TIMEOUT = 20
_UA = u'FineLine IRC bot 0.1 by /u/tdreyer1'
_timeout_message = u'Sorry, reddit is unavailable right now.'
_error_msg = u"That doesn't exist, or reddit is being squirrely."
_bad_reddit_msg = u"That doesn't seem to exist on reddit."
_bad_user_msg = u"That user doesn't seem to exist."
_re_shorturl = re.compile('.*?redd\.it/(\w+)')
_fetch_interval = 100  # Seconds between checking reddit for new posts
_announce_interval = 300  # Seconds between announcing found posts

# Use multiprocess handler for multiple bots on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
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
    try:
        print("trying manual import of colors")
        fp, pathname, description = imp.find_module('colors', [os.path.join('.', '.willie', 'modules')])
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
    finally:
        if fp:
            fp.close()

try:
    import nicks
except:
    import imp
    try:
        print("trying manual import of nicks")
        fp, pathname, description = imp.find_module('nicks', [os.path.join('.', '.willie', 'modules')])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
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
    if 'reddit_lock' not in bot.memory:
        bot.memory['reddit_lock'] = threading.Lock()
    with bot.memory['reddit_lock']:
        if 'reddit-msg_queue' not in bot.memory:
            bot.memory['reddit_msg_queue'] = {}
        bot.memory['reddit-announce'] = {}
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        dbnames = None
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS reddit_list
                           (channel text, subreddit text)''')
            dbcon.commit()
            if not bot.memory['reddit-announce']:
                cur.execute('select channel, subreddit from reddit_list')
                dbnames = cur.fetchall()
        finally:
            cur.close()
            dbcon.close()
        # Prepopulate list of channels
        for c, s in dbnames:
            if c not in bot.memory['reddit-announce']:
                bot.memory['reddit-announce'][c] = {}
                bot.memory['reddit_msg_queue'][c] = []
                bot.memory['reddit_link_history'] = []
            bot.memory['reddit-announce'][c][s] = []
        # Prepopulate list of channels
        # for d in reddits_to_fetch:
        #     bot.memory['reddit-announce'][d] = {}
        # for s in reddits_to_fetch[d]:
        #     bot.memory['reddit-announce'][d][s] = []


@commands('reddit_dump')
def reddit_dump(bot, trigger):
    '''ADMIN: Dumps debug data for the reddit autoannouncer.'''
    if not trigger.owner:
        return
    with bot.memory['reddit_lock']:
        bot.debug(
            __file__,
            log.format(u'reddit-announce length: %i' % len(bot.memory['reddit-announce'])),
            u'always')
        for channel in bot.memory['reddit-announce']:
            bot.debug(__file__, log.format(u'Channel: %s' % channel), u'always')
            bot.debug(
                __file__,
                log.format(u'Channel length: %i' % len(bot.memory['reddit-announce'][channel])),
                u'always')
            for sub in bot.memory['reddit-announce'][channel]:
                bot.debug(
                    __file__,
                    log.format(u'Subreddit: %s' % sub),
                    u'always')
                bot.debug(
                    __file__,
                    log.format(u'Channel length: %i' % len(bot.memory['reddit-announce'][channel][sub])),
                    u'always')
                for id in bot.memory['reddit-announce'][channel][sub]:
                    bot.debug(__file__, log.format(id), u'always')
    # bot.debug(__file__, log.format(u''), u'always')
    bot.reply(u"done")


@commands('reddit_list')
def reddit_list(bot, trigger):
    '''ADMIN: List watched subreddits'''
    if not trigger.owner and not trigger.admin and not trigger.isop:
        return
    with bot.memory['reddit_lock']:
        subs = []
        if bot.memory['reddit-announce']:
            for c in bot.memory['reddit-announce']:
                for s in bot.memory['reddit-announce'][c]:
                    subs.append(s)
                bot.reply(u'Channel: %s Subs: %s' % (c, u', '.join(subs)))
                subs = []
        else:
            bot.reply(u'Not watching any subreddits.')


@commands('reddit_add')
@example('!reddit_add #channel subreddit')
def reddit_add(bot, trigger):
    '''ADMIN: Add watched subreddit.'''
    if not trigger.owner and not trigger.admin and not trigger.isop:
        return
    try:
        channel = trigger.args[1].split()[1]
        sub = trigger.args[1].split()[2]
    except IndexError:
        bot.reply('Malformed input. Takes 2 arguments: Channel and Subreddit')
        return
    with bot.memory['reddit_lock']:
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            cur.execute('''select count(*) from reddit_list
                           where channel = ? and subreddit = ?''',
                        (channel, sub))
            count = cur.fetchall()
            if count[0][0] > 0:
                bot.reply('That already exists')
            else:
                cur.execute('''insert into reddit_list (channel, subreddit)
                               values (?, ?)''', (channel, sub))
                dbcon.commit()
                if channel not in bot.memory['reddit-announce']:
                    bot.memory['reddit-announce'][channel] = {}
                bot.memory['reddit-announce'][channel][sub] = []
                bot.reply('Done.')
        finally:
            cur.close()
            dbcon.close()


@commands('reddit_del')
@example('!reddit_del #channel subreddit')
def reddit_del(bot, trigger):
    '''ADMIN: Remove watched subreddit.'''
    if not trigger.owner and not trigger.admin and not trigger.isop:
        bot.debug(__file__, log.format(trigger.nick, ' just tried to delete a watched subreddit!'), 'warning')
        return
    try:
        channel = trigger.args[1].split()[1]
        sub = trigger.args[1].split()[2]
    except IndexError:
        bot.reply('Malformed input. Takes 2 arguments: Channel and Subreddit')
        return
    with bot.memory['reddit_lock']:
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            cur.execute('''delete from reddit_list
                           where channel = ? and subreddit = ?''',
                        (channel, sub))
            dbcon.commit()
            if channel in bot.memory['reddit-announce'] and sub in bot.memory['reddit-announce'][channel]:
                del bot.memory['reddit-announce'][channel][sub]
                if len(bot.memory['reddit-announce'][channel]) == 0:
                    del bot.memory['reddit-announce'][channel]
            bot.reply('Done.')
        finally:
            cur.close()
            dbcon.close()


@commands('reddit_queue')
def reddit_queue(bot, trigger):
    '''ADMIN: List size of reddit announce queues'''
    if not trigger.owner and not trigger.admin and not trigger.isop:
        return
    for c in bot.memory['reddit_msg_queue']:
        bot.reply('%s: %i' % (c, len(bot.memory['reddit_msg_queue'][c])))


@commands('reddit_queue_del')
def queue_del(bot, trigger):
    '''ADMIN: clears reddit announce queue'''
    if not trigger.owner and not trigger.admin and not trigger.isop:
        bot.debug(__file__, log.format(trigger.nick, ' just tried to clear the reddit queue!'), 'warning')
        return
    bot.memory['reddit_msg_queue'] = {}


@interval(_announce_interval)
def announce_posts(bot, trigger=None):
    with bot.memory['reddit_lock']:
        try:
            for c in bot.memory['reddit_msg_queue']:
                if c in bot.channels and bot.memory['reddit_msg_queue'][c]:
                    # If there is a silencing nick around now, don't announce
                    if util.exists_quieting_nick(bot, c):
                        del bot.memory['reddit_msg_queue'][c][0]
                    else:
                        bot.msg(c, bot.memory['reddit_msg_queue'][c].pop(0))
        except:
            bot.debug(
                __file__,
                log.format(u'Unhandled exception announcing new reddit posts: %s' % sys.exc_info()[0]),
                u'always')
            print(traceback.format_exc())
            return


@interval(_fetch_interval)
@commands('reddit_fetch')
def fetch_reddits(bot, trigger=None):
    '''ADMIN: Manual fetch of the auto-announce posts'''
    if trigger:
        if not trigger.owner and not trigger.admin and not trigger.isop:
            return
    try:
        for channel in bot.memory['reddit-announce']:
            if channel not in bot.channels:
                # Do nothing if not connected to channel
                continue
            for sub in bot.memory['reddit-announce'][channel]:
                fetch_limit = 10
                if not bot.memory['reddit-announce'][channel][sub]:
                    fetch_limit = 1000
                try:
                    posts = [p for p in rc.get_subreddit(sub).get_new(limit=fetch_limit)]
                except timeout:
                    continue
                except:
                    bot.debug(
                        __file__,
                        log.format(u'Unhandled exception when fetching posts: %s [%s]' % (
                            sys.exc_info()[0], trigger.raw)),
                        u"verbose")
                    print(traceback.format_exc())
                    continue
                posts.reverse()
                if not bot.memory['reddit-announce'][channel][sub]:
                    # If our list is empty, we probably have just started up
                    # and don't need to be spammin'
                    bot.memory['reddit-announce'][channel][sub].extend([p.id for p in posts])
                    continue
                for p in posts:
                    if p.id in bot.memory['reddit-announce'][channel][sub]:
                        bot.debug(__file__, log.format(u'found id %s in history' % p.id), 'verbose')
                        continue
                    elif p.created_utc < time.time() - (10 * 60 * 60):
                        bot.debug(__file__, log.format(u'found id %s too old' % p.id), 'verbose')
                        while len(bot.memory['reddit-announce'][channel][sub]) > 1000:
                            bot.memory['reddit-announce'][channel][sub].pop(0)  # Keep list from growing too large
                        bot.memory['reddit-announce'][channel][sub].append(p.id)
                        continue
                    elif p.url in bot.memory['reddit_link_history']:
                        bot.debug(__file__, log.format(u'found matching url for %s, probable crosspost or repost.' % p.id), 'verbose')
                        while len(bot.memory['reddit-announce'][channel][sub]) > 1000:
                            bot.memory['reddit-announce'][channel][sub].pop(0)  # Keep list from growing too large
                        bot.memory['reddit-announce'][channel][sub].append(p.id)
                        continue
                    elif _reurl.search(p.url):
                        bot.debug(__file__, log.format(u'found reddit url for %s, probably a crosspost.' % p.id), 'verbose')
                        while len(bot.memory['reddit-announce'][channel][sub]) > 1000:
                            bot.memory['reddit-announce'][channel][sub].pop(0)  # Keep list from growing too large
                        bot.memory['reddit-announce'][channel][sub].append(p.id)
                        continue
                    else:
                        msg = link_parser(p, url=True, new=True)
                        # If no silencing nicks are around, add the message to
                        # the queue to announce
                        if not util.exists_quieting_nick(bot, channel):
                            bot.memory['reddit_msg_queue'][channel].append(msg)
                        while len(bot.memory['reddit-announce'][channel][sub]) > 1000:
                            bot.memory['reddit-announce'][channel][sub].pop(0)  # Keep list from growing too large
                        bot.memory['reddit-announce'][channel][sub].append(p.id)
                        while len(bot.memory['reddit_link_history']) > 1000:
                            bot.memory['reddit_link_history'].pop(0)
                        bot.memory['reddit_link_history'].append(p.url)
                        bot.debug(
                            __file__,
                            log.format(u'%s %s %s' % (_util_html.unescape(p.title.encode('utf-8')), p.author, p.url)),
                            'verbose')
    except:
        bot.debug(
            __file__,
            log.format(u'Unhandled exception fetching new reddit posts: %s' % sys.exc_info()[0]),
            u'always')
        print(traceback.format_exc())
        return


def link_parser(subm, url=False, new=False):
    '''Takes a praw submission object and returns a formatted string
       When url is True, the URL is included in the formatted string.
       When new is True, the phrasing is appropriate for announcing a
       new post from a subscribed subreddit.
    '''
    page_self = u'Link'
    if subm.is_self:
        page_self = u'Self'
    nsfw = u''
    if subm.over_18:
        nsfw = u'[%s] ' % colors.colorize(u"NSFW", [u"red"], [u"bold"])
    pname = u'[deleted]'
    if subm.author:
        pname = colors.colorize(subm.author.name, [u'purple'])
    score = u'(%s|%sc) ' % (
        colors.colorize(u'↑%s' % str(subm.ups), [u'orange']),
        subm.num_comments
    )
    short_url = u''
    if url:
        short_url = u'%s ' % subm.short_link
    if new:
        return u'/r/%s [ %s] %s%s' % (
            subm.subreddit.display_name,
            short_url,
            nsfw,
            colors.colorize(_util_html.unescape(subm.title), [u'green'])
        )
    else:
        return u'%s%s post %sby %s to /r/%s — %s %s' % (
            nsfw,
            page_self,
            score,
            pname,
            subm.subreddit.display_name,
            colors.colorize(_util_html.unescape(subm.title), [u'green']),
            short_url
        )


@rule(u'(.*?%s)|(.*?%s)' % (_url, _partial))
def reddit_post(bot, trigger):
    """Posts basic info on reddit links"""
    # If you change these, you're going to have to update others too
    user = ur'(^|\s|reddit.com)/u(ser)?/[^/\s)"\'\}\]]{3,20}'
    subm = (u'%s((/r/[^/\s]{3,20}/comments/[^/\s]{3,}(/[^/\s)]{3,})?/?)|'
            u'(/[^/\s)]{4,}/?))') % _url
    cmnt = (u'%s(/r/[^/\s]{3,20}/comments/[^/\s]{3,}/[^/\s]{3,}' +
            '/[^/\s?]{3,}/?)(?:\?context=\d{,2})?') % _url
    subr = u'%s/r/[^/\s)]+/?([\s.!?]|$)' % _url

    def trc(message, length=5):
        '''Truncates messages to a specific word length'''
        m_list = message.split()
        short = message
        if len(m_list) > length:
            short = u' '.join([m_list[elem] for elem in range(length)])
            short = u'%s...' % short.strip()
        if len(short) > 100:
            short = u'%s...' % short.strip('.')[:100]
        return short

    def date_aniv(aniv, day=datetime.now()):
        bot.debug(__file__, log.format(aniv), u'verbose')

        def set_date(year, month, day):
            try:
                date = datetime.strptime(
                    u'%i %i %i' % (year, month, day),
                    u'%Y %m %d'
                )
            except ValueError:
                # Catch leap days and set them appropriately on off years
                date = datetime.strptime(
                    u'%i %i %i' % (year, month, day - 1),
                    u'%Y %m %d'
                )
            return date
        y1, m1, d1 = aniv.strftime(u'%Y %m %d').split()
        y1, m1, d1 = int(y1), int(m1), int(d1)
        y2, m2, d2 = day.strftime(u'%Y %m %d').split()
        y2, m2, d2 = int(y2), int(m2), int(d2)
        if m1 == m2 and d1 == d2:
            diff = 0
        else:
            # Assume neither year is leap year
            if m1 < m2 or (m1 == m2 and d1 < d2):
                y1 = y2 + 1
            else:
                y1 = y2
            aniv = set_date(y1, m1, d1)
            day = set_date(y2, m2, d2)
            diff = aniv - day  # diff is timedelta object
            diff = int(diff.total_seconds() / (24 * 60 * 60))
        return diff
    if re.match(bot.config.core.prefix, trigger.raw):
        return
    try:
        if util.ignore_nick(bot, trigger.nick, trigger.host):
            return

        # Update pay.reddit.com links to work with praw
        link = re.sub('pay\.reddit', 'reddit', trigger.raw, flags=re.I)
        link = re.sub('https', 'http', link, flags=re.I)

        # Fix links that are missing the www. Could be from typo or SSL link
        link = re.sub('://r', '://www.r', link, flags=re.I)

        # User Section
        if re.match(u'.*?%s' % user, link):
            bot.debug(__file__, log.format(u"URL is user"), u"verbose")
            full_url = re.search(
                ur'(https?://)?(www\.)?%s?%s' % (_url, user),
                link
            ).group(0)
            if re.match(u'^/u', full_url):
                full_url = u'http://reddit.com%s' % full_url
            bot.debug(__file__, log.format(u'URL is %s' % full_url), u"verbose")
            # If you change these, you're going to have to update others too
            username = re.split(u"u(ser)?/", full_url)[2].strip(u'/')
            bot.debug(__file__, log.format(u'Username is %s' % username), u"verbose")
            try:
                redditor = rc.get_redditor(username)
            except (InvalidUser):
                bot.say(_bad_user_msg)
                return
            except HTTPError:
                bot.say(_error_msg)
                return
            except timeout:
                bot.say(_timeout_message)
                return
            # Use created date to determine next cake day
            cakeday = datetime.utcfromtimestamp(redditor.created_utc)
            diff_days = date_aniv(cakeday)
            if diff_days == 0:
                cake_message = colors.rainbow(u'HAPPY CAKEDAY!')
            elif diff_days > 0:
                cake_message = u"Cakeday in %i day(s)" % diff_days
            else:
                # oh shit, something went wrong
                cake_message = u""
                bot.debug(__file__, log.format('Date parsing broke!'), 'warning')
            bot.say(u"User %s: Link Karma %i, Comment karma %i, %s" % (
                colors.colorize(redditor.name, [u'purple']),
                redditor.link_karma,
                redditor.comment_karma, cake_message)
            )

        # Comment Section
        elif re.match(u'.*?%s' % cmnt, link):
            bot.debug(__file__, log.format(u"URL is comment"), u"verbose")
            try:
                full_url = u''.join(
                    re.search(ur'(https?://)?(www\.)?%s' % cmnt,
                              link
                              ).groups())
            except TypeError:
                # no match
                return
            if not re.match(u'^http', full_url):
                full_url = u'http://%s' % full_url
            try:
                post = rc.get_submission(url=full_url)
            except HTTPError:
                bot.say(_error_msg)
                return
            except timeout:
                bot.say(_timeout_message)
                return
            comment = post.comments[0]
            nsfw = u''
            if post.over_18:
                nsfw = u'%s post: ' % colors.colorize(u"NSFW", [u"red"], [u"bold"])
            snippet = comment.body
            match = re.compile(ur'\n')  # 2 lines to remove newline markup
            snippet = match.sub(u' ', snippet)
            bot.say(
                u'Comment (↑%s) by %s on %s%s — "%s"' % (
                    colors.colorize(str(comment.ups), [u'orange']),
                    colors.colorize(comment.author.name, [u'purple']),
                    nsfw,
                    trc(_util_html.unescape(colors.colorize(post.title, [u'green'])), 15),
                    trc(_util_html.unescape(colors.colorize(snippet.strip(), [u'teal'])), 15)
                )
            )

        # Submission Section
        elif re.match(u'.*?%s' % subm, link):
            if util.ignore_nick(bot, trigger.nick, trigger.host):
                return
            bot.debug(__file__, log.format(u"URL is submission"), u"verbose")
            full_url = re.search(ur'(https?://)?(www\.)?%s' % subm,
                                 link
                                 ).group(0)
            if not re.match(u'^http', full_url):
                full_url = u'http://%s' % full_url
            bot.debug(__file__, log.format(u"matched is %s" % full_url), u"verbose")
            results = _re_shorturl.search(full_url)
            if results:
                bot.debug(__file__, log.format(u"URL is short"), u'verbose')
                post_id = results.groups()[0]
                bot.debug(__file__, log.format(u'ID is %s' % post_id), u'verbose')
            else:
                bot.debug(__file__, log.format(u'URL is %s' % full_url), u"verbose")
            try:
                if results:
                    page = rc.get_submission(submission_id=post_id)
                else:
                    page = rc.get_submission(full_url)
            except HTTPError:
                bot.say(_error_msg)
                return
            except timeout:
                bot.say(_timeout_message)
                return
            msg = link_parser(page)
            bot.say(msg)

        # Subreddit Section
        elif re.match(u'.*?%s' % subr, link):
            bot.debug(__file__, log.format(u"URL is subreddit"), u"verbose")
            full_url = re.search(ur'(https?://)?(www\.)?%s' % subr,
                                 link
                                 ).group(0)
            bot.debug(__file__, log.format(u'URL is %s' % full_url), u"verbose")
            # TODO pull back and display appropriate information for this.
            # I honestly don't know what useful info there is here!
            # So here's a stub
            sub_name = full_url.strip(u'/').rpartition(u'/')[2]
            bot.debug(__file__, log.format(sub_name), u"verbose")
            try:
                # sub = rc.get_subreddit(sub_name)
                pass
            except InvalidSubreddit:
                # bot.say(_bad_reddit_msg)
                return
            except HTTPError:
                # bot.say(_error_msg)
                return
            except timeout:
                # bot.say(_timeout_message)
                return
            # do stuff?
        # Invalid URL Section
        else:
            bot.debug(__file__, log.format(u"Matched URL is invalid"), u"warning")
            # fail silently
    except:
        bot.debug(
            __file__,
            log.format(u'Unhandled exception parsing reddit link: %s' % sys.exc_info()[0]),
            u'always')
        print(traceback.format_exc())
        return


if __name__ == "__main__":
    print(__doc__.strip())
