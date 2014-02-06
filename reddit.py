# coding=utf8
"""
reddit.py - A simple Willie module that provides reddit functionality
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

Depends on PRAW: https://github.com/praw-dev/praw
"""
#TODO Filter multiple posts from a single user (ie. one user posts 10x in 10 min)
#TODO Increase initial buffer fill to 1000
#TODO add recency filter for announced reddit posts
import re
from datetime import datetime
#from urllib2 import HTTPError
from socket import timeout
import imp
import sys
import threading

import praw
import praw.errors
from praw.errors import InvalidUser, InvalidSubreddit
from requests import HTTPError

from willie.tools import Nick
from willie.module import commands, rule, interval

_url = u'(reddit\.com|redd\.it)'
_partial = ur'((^|[^A-Za-z0-9])/(r|u(ser)?)/[^/\s\.]{3,20})'
_TIMEOUT = 20
_UA = u'FineLine IRC bot 0.1 by /u/tdreyer1'
_timeout_message = u'Sorry, reddit is unavailable right now.'
_error_msg = u"That doesn't exist, or reddit is being squirrely."
_bad_reddit_msg = u"That doesn't seem to exist on reddit."
_bad_user_msg = u"That user doesn't seem to exist."
_ignore = [Nick(r'hushmachine.*'), Nick(r'tmoister1')]
_re_shorturl = re.compile('.*?redd\.it/(\w+)')
_fetch_quiet = ['hushmachine', 'hushmachine_mk2', 'hushbot']
_fetch_interval = 100  # Seconds between checking reddit for new posts
_announce_interval = 300  # Seconds between announcing found posts

#Use multiprocess handler for multiple bots on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import colors
except:
    try:
        print "trying manual import of colors"
        fp, pathname, description = imp.find_module('colors',
                                                    ['./.willie/modules/']
                                                    )
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
    finally:
        if fp:
            fp.close()
try:
    import nicks
except:
    try:
        print "trying manual import of nicks"
        fp, pathname, description = imp.find_module('nicks',
                                                    ['./.willie/modules/']
                                                    )
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()


def setup(bot):
    if 'reddit_lock' not in bot.memory:
        bot.memory['reddit_lock'] = threading.Lock()
    with bot.memory['reddit_lock']:
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
            bot.memory['reddit-announce'][c][s] = []
        # Prepopulate list of channels
        #for d in reddits_to_fetch:
        #    bot.memory['reddit-announce'][d] = {}
        #    for s in reddits_to_fetch[d]:
        #        bot.memory['reddit-announce'][d][s] = []


@commands('reddit_dump')
def reddit_dump(bot, trigger):
    '''ADMIN: Dumps debug data for the reddit autoannouncer.'''
    if not trigger.owner:
        return
    with bot.memory['reddit_lock']:
        bot.debug(u'>', u'reddit-announce length: %i' % len(bot.memory['reddit-announce']), u'always')
        for channel in bot.memory['reddit-announce']:
            bot.debug(u'>>>', u'Channel: %s' % channel, u'always')
            bot.debug(u'>>>', u'Channel length: %i' % len(bot.memory['reddit-announce'][channel]), u'always')
            for sub in bot.memory['reddit-announce'][channel]:
                bot.debug(u'>>>>>>', u'Subreddit: %s' % sub, u'always')
                bot.debug(u'>>>>>>', u'Channel length: %i' % len(bot.memory['reddit-announce'][channel][sub]), u'always')
                for id in bot.memory['reddit-announce'][channel][sub]:
                    bot.debug(u'>>>>>>>>>', id, u'always')
    #bot.debug(u'>>>', u'', u'always')
    bot.reply(u"done")


@commands('reddit_list')
def reddit_list(bot, trigger):
    '''ADMIN: List watched subreddits'''
    if not trigger.owner:
        return
    with bot.memory['reddit_lock']:
        subs = []
        for c in bot.memory['reddit-announce']:
            for s in bot.memory['reddit-announce'][c]:
                subs.append(s)
            bot.reply(u'Channel: %s Subs: %s' % (c, u', '.join(subs)))
            subs = []


@commands('reddit_add')
def reddit_add(bot, trigger):
    '''ADMIN: Add watched subreddit. Syntax = #Channel subredditname'''
    if not trigger.owner:
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
def reddit_del(bot, trigger):
    '''ADMIN: Remove watched subreddit. Syntax = #Channel subredditname'''
    if not trigger.owner:
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
    '''ADMIN: List watched subreddits'''
    if not trigger.owner:
        return
    for c in bot.memory['reddit_msg_queue']:
        bot.reply('%s: %i' % (c, len(bot.memory['reddit_msg_queue'][c])))


@interval(_announce_interval)
def announce_posts(bot, trigger=None):
    with bot.memory['reddit_lock']:
        for c in bot.memory['reddit_msg_queue']:
            if c in bot.channels and bot.memory['reddit_msg_queue'][c]:
                bot.msg(c, bot.memory['reddit_msg_queue'][c].pop(0))


@interval(_fetch_interval)
@commands('fetch')
def fetch_reddits(bot, trigger=None):
    try:
        for channel in bot.memory['reddit-announce']:
            if channel not in bot.channels:
                # Do nothing if not connected to channel
                return
            for n in _fetch_quiet:
                # Shutup
                if nicks.in_chan(bot, channel, n):
                    return
            bot.debug(u'reddit.fetch', u'channel = %s' % channel, 'verbose')
            for sub in bot.memory['reddit-announce'][channel]:
                bot.debug(u'reddit.fetch', u'sub = %s' % sub, 'verbose')
                try:
                    posts = [p for p in rc.get_subreddit(sub).get_new(limit=10)]
                # may need additional exceptions here for malformed pages
                except timeout:
                    pass
                except:
                    bot.debug(u"reddit:fetch",
                              u'Unhandled exception: %s [%s]' % (sys.exc_info()[0], trigger.bytes),
                              u"verbose"
                              )
                    return

                if not bot.memory['reddit-announce'][channel][sub]:
                    # If our list is empty, we probably have just started up
                    # and don't need to be spammin'
                    bot.debug(u'reddit.fetch', u'Initializing history', 'verbose')
                    bot.memory['reddit-announce'][channel][sub].extend([p.id for p in posts])
                    return
                posts.reverse()
                for p in posts:
                    if p.id not in bot.memory['reddit-announce'][channel][sub]:
                        try:
                            page = rc.get_submission(submission_id=p.id)
                        except HTTPError:
                            bot.debug(u'reddit:fetch_reddits',
                                      _error_msg,
                                      u'verbose')
                            return
                        except timeout:
                            bot.debug(u'reddit:fetch_reddits',
                                      _timeout_message,
                                      u'verbose')
                            return
                        except:
                            bot.debug(u"reddit:fetch",
                                      u'Unhandled exception: %s [%s]' % (sys.exc_info()[0], trigger.bytes),
                                      u"verbose"
                                      )
                            return
                        msg = link_parser(page, url=True, new=True)
                        bot.memory['reddit_msg_queue'][channel].append(msg)
                        bot.debug(u'reddit.fetch', u'%s %s %s' % (p.title, p.author, p.url), 'verbose')
                        bot.memory['reddit-announce'][channel][sub].append(p.id)
                        if len(bot.memory['reddit-announce'][channel][sub]) > 1000:
                            bot.memory['reddit-announce'][channel][sub].pop(0)  # Keep list from growing too large
                    else:
                        bot.debug(u'reddit.fetch', u'found id %s in history' % p.id, 'verbose')
    except:
        bot.debug(u'reddit:fetch',
                  u'Unhandled exception: %s' % sys.exc_info()[0],
                  u'always')
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
    #newpost = ''
    #if new:
        #newpost = 'New '
        #page_self = page_self.lower()
    nsfw = u''
    if subm.over_18:
        nsfw = u'[%s] ' % colors.colorize(u"NSFW", [u"red"], [u"bold"])
    pname = u'[deleted]'
    if subm.author:
        pname = colors.colorize(subm.author.name, [u'purple'])
    score = u'(%s|%s|%sc) ' % (
        colors.colorize(u'↑%s' % str(subm.ups), [u'orange']),
        colors.colorize(u'↓%s' % str(subm.downs), [u'navy']),
        subm.num_comments
    )
    short_url = u''
    if url:
        score = u''
        short_url = u'[ %s ]' % subm.short_link
    if new:
        return u'%s%s New %s post to /r/%s — %s' % (
            short_url,
            nsfw,
            page_self.lower(),
            subm.subreddit.display_name,
            colors.colorize(subm.title, [u'green'])
        )
    else:
        return u'%s%s post %sby %s to /r/%s — %s %s' % (
            #newpost,
            nsfw,
            page_self,
            score,
            pname,
            subm.subreddit.display_name,
            colors.colorize(subm.title, [u'green']),
            short_url
        )


@rule(u'(.*?%s)|(.*?%s)' % (_url, _partial))
def reddit_post(bot, trigger):
    """Posts basic info on reddit links"""
    #If you change these, you're going to have to update others too
    user = ur'/u(ser)?/[^/\s)"\'\}\]]{3,20}'
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
        bot.debug(u'reddit.py:date_aniv', aniv, u'verbose')

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
            #Assume neither year is leap year
            if m1 < m2 or (m1 == m2 and d1 < d2):
                y1 = y2 + 1
            else:
                y1 = y2
            aniv = set_date(y1, m1, d1)
            day = set_date(y2, m2, d2)
            diff = aniv - day  # diff is timedelta object
            diff = int(diff.total_seconds() / (24 * 60 * 60))
        return diff

    trigger_nick = Nick(trigger.nick)
    for i in _ignore:
        if i == trigger_nick:
            return

    # User Section
    if re.match(u'.*?%s' % user, trigger.bytes):
        bot.debug(u"reddit:reddit_post", u"URL is user", u"verbose")
        full_url = re.search(
            ur'(https?://)?(www\.)?%s?%s' % (_url, user),
            trigger.bytes
        ).group(0)
        if re.match(u'^/u', full_url):
            full_url = u'http://reddit.com%s' % full_url
        bot.debug(u"reddit:reddit_post",
                  u'URL is %s' % full_url,
                  u"verbose"
                  )
        # If you change these, you're going to have to update others too
        username = re.split(
            u"reddit\.com/u(ser)?/",
            full_url
        )[2].strip(u'/')
        bot.debug(u"reddit:reddit_post",
                  u'Username is %s' % username,
                  u"verbose"
                  )
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
        except:
            bot.debug(u'reddit:redditor',
                      u'Unhandled exception: %s [%s]' % (sys.exc_info()[0], trigger.bytes),
                      u'always')
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
            bot.debug('reddit:reddit_post',
                      'Date parsing broke!',
                      'warning'
                      )
        bot.say(u"User %s: Link Karma %i, Comment karma %i, %s" % (
            colors.colorize(redditor.name, [u'purple']),
            redditor.link_karma,
            redditor.comment_karma, cake_message)
        )

    # Comment Section
    elif re.match(u'.*?%s' % cmnt, trigger.bytes):
        bot.debug(u"reddit:reddit_post", u"URL is comment", u"verbose")
        try:
            full_url = u''.join(
                re.search(ur'(https?://)?(www\.)?%s' % cmnt,
                          trigger.bytes
                          ).groups())
        except TypeError:
            #no match
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
        except:
            bot.debug(u'reddit:comment',
                      u'Unhandled exception: %s [%s]' % (sys.exc_info()[0], trigger.bytes),
                      u'always')
            return
        comment = post.comments[0]
        nsfw = u''
        if post.over_18:
            nsfw = u'%s post: ' % colors.colorize(u"NSFW", [u"red"], [u"bold"])
        snippet = comment.body
        match = re.compile(ur'\n')  # 2 lines to remove newline markup
        snippet = match.sub(u' ', snippet)
        snippet = trc(snippet, 15)
        bot.say(
            u'Comment (↑%s|↓%s) by %s on %s%s — "%s"' % (
                colors.colorize(str(comment.ups), [u'green']),
                colors.colorize(str(comment.downs), [u'orange']),
                colors.colorize(comment.author.name, [u'purple']),
                nsfw,
                trc(post.title, 15),
                colors.colorize(snippet.strip(), [u'blue'])
            )
        )

    # Submission Section
    elif re.match(u'.*?%s' % subm, trigger.bytes):
        for n in _ignore:
            if re.match(u'%s.*?' % n, trigger.nick):
                return
        bot.debug(u"reddit:reddit_post", u"URL is submission", u"verbose")
        full_url = re.search(ur'(https?://)?(www\.)?%s' % subm,
                             trigger.bytes
                             ).group(0)
        if not re.match(u'^http', full_url):
            full_url = u'http://%s' % full_url
        bot.debug(u"reddit:reddit_post",
                  u"matched is %s" % full_url,
                  u"verbose"
                  )
        results = _re_shorturl.search(full_url)
        if results:
            bot.debug(u"reddit:reddit_post", u"URL is short", u'verbose')
            post_id = results.groups()[0]
            bot.debug(u'reddit:reddit_post',
                      u'ID is %s' % post_id,
                      u'verbose')
        else:
            bot.debug(u"reddit:reddit_post",
                      u'URL is %s' % full_url,
                      u"verbose")
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
        except:
            bot.debug(u'reddit:post',
                      u'Unhandled exception: %s [%s]' % (sys.exc_info()[0], trigger.bytes),
                      u'always')
            return
        msg = link_parser(page)
        bot.say(msg)

    # Subreddit Section
    elif re.match(u'.*?%s' % subr, trigger.bytes):
        bot.debug(u"reddit:reddit_post", u"URL is subreddit", u"verbose")
        full_url = re.search(ur'(https?://)?(www\.)?%s' % subr,
                             trigger.bytes
                             ).group(0)
        bot.debug(u"reddit:reddit_post",
                  u'URL is %s' % full_url,
                  u"verbose"
                  )
        # TODO pull back and display appropriate information for this.
        # I honestly don't know what useful info there is here!
        # So here's a stub
        sub_name = full_url.strip(u'/').rpartition(u'/')[2]
        bot.debug(u"reddit:reddit_post", sub_name, u"verbose")
        try:
            #sub = rc.get_subreddit(sub_name)
            pass
        except InvalidSubreddit:
            #bot.say(_bad_reddit_msg)
            return
        except HTTPError:
            #bot.say(_error_msg)
            return
        except timeout:
            #bot.say(_timeout_message)
            return
        except:
            bot.debug(u'reddit:subreddit',
                      u'Unhandled exception: %s [%s]' % (sys.exc_info()[0], trigger.bytes),
                      u'always')
            return
        #do stuff?
    # Invalid URL Section
    else:
        bot.debug(u"reddit:reddit_post",
                  u"Matched URL is invalid",
                  u"warning"
                  )
        #fail silently


if __name__ == "__main__":
    print __doc__.strip()
