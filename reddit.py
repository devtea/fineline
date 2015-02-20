"""
reddit.py - A simple Willie module that provides reddit functionality
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

Depends on PRAW: https://github.com/praw-dev/praw
"""
# TODO Filter multiple posts from a single user (ie. one user posts 10x in 10 min)
# TODO add recency filter for announced reddit posts
import re
import threading
import time
from datetime import datetime
from html import unescape
from socket import timeout

import praw
import praw.errors
from praw.errors import InvalidUser, InvalidSubreddit
from requests import HTTPError

from willie.logger import get_logger
from willie.module import commands, rule, interval, example

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
try:
    import colors
except:
    import sys
    import os.path
    sys.path.append(os.path.join('.', '.willie', 'modules'))
    import colors
    if 'colors' not in sys.modules:
        sys.modules['colors'] = colors
try:
    import nicks
except:
    import sys
    import os.path
    sys.path.append(os.path.join('.', '.willie', 'modules'))
    import nicks
    if 'nicks' not in sys.modules:
        sys.modules['nicks'] = nicks
try:
    import util
except:
    import sys
    import os.path
    sys.path.append(os.path.join('.', '.willie', 'modules'))
    import util
    if 'util' not in sys.modules:
        sys.modules['util'] = util

LOGGER = get_logger(__name__)
_url = '(reddit\.com|redd\.it)'
_reurl = re.compile(_url, flags=re.I)
_partial = r'((^|[^A-Za-z0-9])/(r|u(ser)?)/[^/\s\.]{3,20})'
_TIMEOUT = 20
_UA = 'FineLine 5.0 by /u/tdreyer1'
_timeout_message = 'Sorry, reddit is unavailable right now.'
_error_msg = "That doesn't exist, or reddit is being squirrely."
_bad_reddit_msg = "That doesn't seem to exist on reddit."
_bad_user_msg = "That user doesn't seem to exist."
_re_shorturl = re.compile('.*?redd\.it/(\w+)')
_fetch_interval = 100  # Seconds between checking reddit for new posts
_announce_interval = 300  # Seconds between announcing found posts

# Use multiprocess handler for multiple bots on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)


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
        LOGGER.warning(log.format('reddit-announce length: %i' % len(bot.memory['reddit-announce'])))
        for channel in bot.memory['reddit-announce']:
            LOGGER.warning(log.format('Channel: %s' % channel))
            LOGGER.warning(log.format('Channel length: %i' % len(bot.memory['reddit-announce'][channel])))
            for sub in bot.memory['reddit-announce'][channel]:
                LOGGER.warning(log.format('Subreddit: %s' % sub),)
                LOGGER.warning(log.format('Channel length: %i' % len(bot.memory['reddit-announce'][channel][sub])))
                for id in bot.memory['reddit-announce'][channel][sub]:
                    LOGGER.warning(log.format(id))
    # LOGGER.warning(log.format(''))
    bot.reply("done")


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
                bot.reply('Channel: %s Subs: %s' % (c, ', '.join(subs)))
                subs = []
        else:
            bot.reply('Not watching any subreddits.')


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
        LOGGER.warning(log.format(trigger.nick, ' just tried to delete a watched subreddit!'))
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
        LOGGER.warning(log.format(trigger.nick, ' just tried to clear the reddit queue!'))
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
            LOGGER.error(log.format('Unhandled exception announcing new reddit posts'), exc_info=True)


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
                    LOGGER.warning(log.format('Timeout when fetching from reddit for auto announce'))
                    continue
                except:
                    LOGGER.error(log.format('Unhandled exception when fetching posts: [%s]'), trigger, exc_info=True)
                    continue
                posts.reverse()
                if not bot.memory['reddit-announce'][channel][sub]:
                    # If our list is empty, we probably have just started up
                    # and don't need to be spammin'
                    bot.memory['reddit-announce'][channel][sub].extend([p.id for p in posts])
                    continue
                for p in posts:
                    if p.id in bot.memory['reddit-announce'][channel][sub]:
                        LOGGER.info(log.format('found id %s in history'), p.id)
                        continue
                    elif p.created_utc < time.time() - (10 * 60 * 60):
                        LOGGER.info(log.format('found id %s too old'), p.id)
                        while len(bot.memory['reddit-announce'][channel][sub]) > 1000:
                            bot.memory['reddit-announce'][channel][sub].pop(0)  # Keep list from growing too large
                        bot.memory['reddit-announce'][channel][sub].append(p.id)
                        continue
                    elif p.url in bot.memory['reddit_link_history']:
                        LOGGER.info(log.format('found matching url for %s, probable crosspost or repost.'), p.id)
                        while len(bot.memory['reddit-announce'][channel][sub]) > 1000:
                            bot.memory['reddit-announce'][channel][sub].pop(0)  # Keep list from growing too large
                        bot.memory['reddit-announce'][channel][sub].append(p.id)
                        continue
                    elif _reurl.search(p.url):
                        LOGGER.info(log.format('found reddit url for %s, probably a crosspost.'), p.id)
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
                        LOGGER.info(log.format('%s %s %s'), unescape(p.title.encode('utf-8')), p.author, p.url)
    except:
        LOGGER.error(log.format('Unhandled exception fetching new reddit posts'), exc_info=True)


def link_parser(subm, url=False, new=False):
    '''Takes a praw submission object and returns a formatted string
       When url is True, the URL is included in the formatted string.
       When new is True, the phrasing is appropriate for announcing a
       new post from a subscribed subreddit.
    '''
    page_self = 'Link'
    if subm.is_self:
        page_self = 'Self'
    nsfw = ''
    if subm.over_18:
        nsfw = '[%s] ' % colors.colorize("NSFW", ["red"], ["bold"])
    pname = '[deleted]'
    if subm.author:
        pname = colors.colorize(subm.author.name, ['purple'])
    score = '(%s|%sc) ' % (
        colors.colorize('↑%s' % str(subm.ups), ['orange']),
        subm.num_comments
    )
    short_url = ''
    if url:
        short_url = '%s ' % subm.short_link
    if new:
        return '/r/%s [ %s] %s%s' % (
            subm.subreddit.display_name,
            short_url,
            nsfw,
            colors.colorize(unescape(subm.title), ['green'])
        )
    else:
        return '%s%s post %sby %s to /r/%s — %s %s' % (
            nsfw,
            page_self,
            score,
            pname,
            subm.subreddit.display_name,
            colors.colorize(unescape(subm.title), ['green']),
            short_url
        )


@rule('(.*?%s)|(.*?%s)' % (_url, _partial))
def reddit_post(bot, trigger):
    """Posts basic info on reddit links"""
    # If you change these, you're going to have to update others too
    user = r'(^|\s|reddit.com)/u(ser)?/[^/\s)"\'\}\]]{3,20}'
    subm = ('%s((/r/[^/\s]{3,20}/comments/[^/\s]{3,}(/[^/\s)]{3,})?/?)|'
            '(/[^/\s)]{4,}/?))') % _url
    cmnt = ('%s(/r/[^/\s]{3,20}/comments/[^/\s]{3,}/[^/\s]{3,}' +
            '/[^/\s?]{3,}/?)(?:\?context=\d{,2})?') % _url
    subr = '%s/r/[^/\s)]+/?([\s.!?]|$)' % _url

    def trc(message, length=5):
        '''Truncates messages to a specific word length'''
        m_list = message.split()
        short = message
        if len(m_list) > length:
            short = ' '.join([m_list[elem] for elem in range(length)])
            short = '%s...' % short.strip()
        if len(short) > 100:
            short = '%s...' % short.strip('.')[:100]
        return short

    def date_aniv(aniv, day=datetime.now()):
        LOGGER.info(log.format(aniv))

        def set_date(year, month, day):
            try:
                date = datetime.strptime(
                    '%i %i %i' % (year, month, day),
                    '%Y %m %d'
                )
            except ValueError:
                # Catch leap days and set them appropriately on off years
                date = datetime.strptime(
                    '%i %i %i' % (year, month, day - 1),
                    '%Y %m %d'
                )
            return date
        y1, m1, d1 = aniv.strftime('%Y %m %d').split()
        y1, m1, d1 = int(y1), int(m1), int(d1)
        y2, m2, d2 = day.strftime('%Y %m %d').split()
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
    if re.match(bot.config.core.prefix, trigger):
        return
    try:
        if util.ignore_nick(bot, trigger.nick, trigger.host):
            return

        # Update pay.reddit.com links to work with praw
        link = re.sub('pay\.reddit', 'reddit', trigger, flags=re.I)
        link = re.sub('https', 'http', link, flags=re.I)

        # Fix links that are missing the www. Could be from typo or SSL link
        link = re.sub('://r', '://www.r', link, flags=re.I)

        # User Section
        if re.match('.*?%s' % user, link):
            LOGGER.info(log.format("URL is user"))
            full_url = re.search(
                r'(https?://)?(www\.)?%s?%s' % (_url, user),
                link
            ).group(0)
            if re.match('^/u', full_url):
                full_url = 'http://reddit.com%s' % full_url
            LOGGER.info(log.format('URL is %s'), full_url)
            # If you change these, you're going to have to update others too
            username = re.split("u(ser)?/", full_url)[2].strip('/')
            LOGGER.info(log.format('Username is %s'), username)
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
                cake_message = colors.rainbow('HAPPY CAKEDAY!')
            elif diff_days > 0:
                cake_message = "Cakeday in %i day(s)" % diff_days
            else:
                # oh shit, something went wrong
                cake_message = ""
                LOGGER.error(log.format('Date parsing broke!'))
            bot.say("User %s: Link Karma %i, Comment karma %i, %s" % (
                colors.colorize(redditor.name, ['purple']),
                redditor.link_karma,
                redditor.comment_karma, cake_message)
            )

        # Comment Section
        elif re.match('.*?%s' % cmnt, link):
            LOGGER.info(log.format("URL is comment"))
            try:
                full_url = ''.join(
                    re.search(r'(https?://)?(www\.)?%s' % cmnt,
                              link
                              ).groups())
            except TypeError:
                # no match
                return
            if not re.match('^http', full_url):
                full_url = 'http://%s' % full_url
            try:
                post = rc.get_submission(url=full_url)
            except HTTPError:
                bot.say(_error_msg)
                return
            except timeout:
                bot.say(_timeout_message)
                return
            comment = post.comments[0]
            nsfw = ''
            if post.over_18:
                nsfw = '%s post: ' % colors.colorize("NSFW", ["red"], ["bold"])
            snippet = comment.body
            match = re.compile(r'\n')  # 2 lines to remove newline markup
            snippet = match.sub(' ', snippet)
            bot.say(
                'Comment (↑%s) by %s on %s%s — "%s"' % (
                    colors.colorize(str(comment.ups), ['orange']),
                    colors.colorize(comment.author.name, ['purple']),
                    nsfw,
                    trc(unescape(colors.colorize(post.title, ['green'])), 15),
                    trc(unescape(colors.colorize(snippet.strip(), ['teal'])), 15)
                )
            )

        # Submission Section
        elif re.match('.*?%s' % subm, link):
            if util.ignore_nick(bot, trigger.nick, trigger.host):
                return
            LOGGER.info(log.format("URL is submission"))
            full_url = re.search(r'(https?://)?(www\.)?%s' % subm,
                                 link
                                 ).group(0)
            if not re.match('^http', full_url):
                full_url = 'http://%s' % full_url
            LOGGER.info(log.format("matched is %s"), full_url)
            results = _re_shorturl.search(full_url)
            if results:
                LOGGER.info(log.format("URL is short"))
                post_id = results.groups()[0]
                LOGGER.info(log.format('ID is %s'), post_id)
            else:
                LOGGER.info(log.format('URL is %s'), full_url)
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
        elif re.match('.*?%s' % subr, link):
            LOGGER.info(log.format("URL is subreddit"))
            full_url = re.search(r'(https?://)?(www\.)?%s' % subr,
                                 link
                                 ).group(0)
            LOGGER.info(log.format('URL is %s'), full_url)
            # TODO pull back and display appropriate information for this.
            # I honestly don't know what useful info there is here!
            # So here's a stub
            sub_name = full_url.strip('/').rpartition('/')[2]
            LOGGER.info(log.format(sub_name))
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
            LOGGER.warning(log.format("Matched URL is invalid"))
            # fail silently
    except:
        LOGGER.error(log.format('Unhandled exception parsing reddit link: %s'), exc_info=True)


if __name__ == "__main__":
    print(__doc__.strip())
