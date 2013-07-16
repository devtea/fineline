# coding=utf8
"""
reddit.py - A simple Willie module that provides reddit functionality
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import re
import time
from datetime import datetime
#from urllib2 import HTTPError
from socket import timeout

import praw
import praw.errors
from praw.errors import InvalidUser, InvalidSubreddit
from requests import HTTPError

from colors import *
from willie import web
from willie.module import commands, rule, rate

_url = u'(reddit\.com|redd\.it)'
_partial = ur'((^|[^A-Za-z0-9])/(r|u(ser)?)/[^/\s\.]{3,20})'
_ignore = [u'hushmachine', u'tmoister1']
_TIMEOUT = 20
_UA = u'FineLine IRC bot 0.1 by /u/tdreyer1'
_timeout_message = u'Sorry, reddit is unavailable right now.'
_bad_reddit_msg = u"That doesn't seem to exist on reddit."
_bad_user_msg = u"That user doesn't seem to exist."
_error_msg = u"That doesn't exist, or reddit is being squirrely."

#Use multiprocess handler for multiple bots on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)


@rule(u'(.*?%s)|(.*?%s)' % (_url, _partial))
def reddit_post(Willie, trigger):
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
        Willie.debug(u'reddit.py:date_aniv', aniv, u'verbose')

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

    # User Section
    if re.match(u'.*?%s' % user, trigger.bytes):
        Willie.debug(u"reddit:reddit_post", u"URL is user", u"verbose")
        full_url = re.search(
            ur'(https?://)?(www\.)?%s?%s' % (_url, user),
            trigger.bytes
        ).group(0)
        if re.match(u'^/u', full_url):
            full_url = u'http://reddit.com%s' % full_url
        Willie.debug(u"reddit:reddit_post",
                     u'URL is %s' % full_url,
                     u"verbose"
                     )
        # If you change these, you're going to have to update others too
        username = re.split(
            u"reddit\.com/u(ser)?/",
            full_url
        )[2].strip(u'/')
        Willie.debug(u"reddit:reddit_post",
                     u'Username is %s' % username,
                     u"verbose"
                     )
        try:
            redditor = rc.get_redditor(username)
        except (InvalidUser):
            Willie.say(_bad_user_msg)
            return
        except HTTPError:
            Willie.say(_error_msg)
            return
        except timeout:
            Willie.say(_timeout_message)
            return
        # Use created date to determine next cake day
        cakeday = datetime.utcfromtimestamp(redditor.created_utc)
        diff_days = date_aniv(cakeday)
        if diff_days == 0:
            cake_message = rainbow(u'HAPPY CAKEDAY!')
        elif diff_days > 0:
            cake_message = u"Cakeday in %i day(s)" % diff_days
        else:
            # oh shit, something went wrong
            cake_message = u""
            Willie.debug('reddit:reddit_post',
                         'Date parsing broke!',
                         'warning'
                         )
        Willie.say(u"User %s: Link Karma %i, Comment karma %i, %s" % (
            colorize(redditor.name, [u'purple']),
            redditor.link_karma,
            redditor.comment_karma, cake_message)
        )

    # Comment Section
    elif re.match(u'.*?%s' % cmnt, trigger.bytes):
        Willie.debug(u"reddit:reddit_post", u"URL is comment", u"verbose")
        full_url = u''.join(
            re.search(ur'(https?://)?(www\.)?%s' % cmnt,
                      trigger.bytes
                      ).groups())
        if not re.match(u'^http', full_url):
            full_url = u'http://%s' % full_url
        try:
            post = rc.get_submission(url=full_url)
        except HTTPError:
            Willie.say(_error_msg)
            return
        except timeout:
            Willie.say(_timeout_message)
            return
        comment = post.comments[0]
        #Willie.debug("reddit:reddit_post", pprint(vars(post)), "verbose")
        nsfw = u''
        if post.over_18:
            nsfw = u'%s post: ' % colorize(u"NSFW", [u"red"], [u"bold"])
        snippet = comment.body
        match = re.compile(ur'\n')  # 2 lines to remove newline markup
        snippet = match.sub(u' ', snippet)
        snippet = trc(snippet, 15)
        Willie.say(
            u'Comment (↑%s|↓%s) by %s on %s%s — "%s"' % (
                colorize(str(comment.ups), [u'green']),
                colorize(str(comment.downs), [u'orange']),
                colorize(comment.author.name, [u'purple']),
                nsfw,
                trc(post.title, 15),
                colorize(snippet.strip(), [u'navy'])
            )
        )

    # Submission Section
    elif re.match(u'.*?%s' % subm, trigger.bytes):
        for n in _ignore:
            if re.match(u'%s.*?' % n, trigger.nick):
                return
        Willie.debug(u"reddit:reddit_post", u"URL is submission", u"verbose")
        full_url = re.search(ur'(https?://)?(www\.)?%s' % subm,
                             trigger.bytes
                             ).group(0)
        if not re.match(u'^http', full_url):
            full_url = u'http://%s' % full_url
        Willie.debug(u"reddit:reddit_post",
                     u"matched is %s" % full_url,
                     u"verbose"
                     )
        if re.match(u'.*?redd\.it', full_url):
            Willie.debug(u"reddit:reddit_post", u"URL is short", u'verbose')
            try:
                full_url = web.get_urllib_object(full_url, _TIMEOUT).geturl()
            except InvalidSubreddit:
                Willie.say(_bad_reddit_msg)
                return
            except HTTPError:
                Willie.say(_error_msg)
                return
            except timeout:
                Willie.say(_timeout_message)
                return
        Willie.debug(u"reddit:reddit_post",
                     u'URL is %s' % full_url,
                     u"verbose"
                     )
        try:
            page = rc.get_submission(full_url)
        except HTTPError:
            Willie.say(_error_msg)
            return
        except timeout:
            Willie.say(_timeout_message)
            return
        page_self = u'Link'
        if page.is_self:
            page_self = u'Self'
        nsfw = u''
        if page.over_18:
            nsfw = u'[%s] ' % colorize(u"NSFW", [u"red"], [u"bold"])
        Willie.say(
            u'%s%s post (↑%s|↓%s|%sc) by %s to %s — %s' % (
                nsfw,
                page_self,
                colorize(str(page.ups), [u'green']),
                colorize(str(page.downs), [u'orange']),
                page.num_comments,
                colorize(page.author.name, [u'purple']),
                page.subreddit.display_name,
                colorize(page.title, [u'navy'])
            )
        )

    # Subreddit Section
    elif re.match(u'.*?%s' % subr, trigger.bytes):
        Willie.debug(u"reddit:reddit_post", u"URL is subreddit", u"verbose")
        full_url = re.search(ur'(https?://)?(www\.)?%s' % subr,
                             trigger.bytes
                             ).group(0)
        Willie.debug(u"reddit:reddit_post",
                     u'URL is %s' % full_url,
                     u"verbose"
                     )
        # TODO pull back and display appropriate information for this.
        # I honestly don't know what useful info there is here!
        # So here's a stub
        sub_name = full_url.strip(u'/').rpartition(u'/')[2]
        Willie.debug(u"reddit:reddit_post", sub_name, u"verbose")
        try:
            sub = rc.get_subreddit(sub_name)
        except InvalidSubreddit:
            #Willie.say(_bad_reddit_msg)
            return
        except HTTPError:
            #Willie.say(_error_msg)
            return
        except timeout:
            #Willie.say(_timeout_message)
            return
        #do stuff?
    # Invalid URL Section
    else:
        Willie.debug(u"reddit:reddit_post",
                     u"Matched URL is invalid",
                     u"warning"
                     )
        #fail silently


@commands(u'queue', u'check', u'posts', u'que', u'crit', u'critique')
@rate(120)
def mlpds_check(Willie, trigger):
    '''Checks for posts within the last 48h with fewer than 2 comments'''
    try:
        mlpds = rc.get_subreddit(u'MLPDrawingSchool')
    except InvalidSubreddit:
        Willie.say(_bad_reddit_msg)
        return
    except HTTPError:
        Willie.say(_error_msg)
        return
    except timeout:
        Willie.say(_timeout_message)
        return
    new_posts = mlpds.get_new(limit=50)
    #Willie.debug("reddit:mlpds_check", pprint(dir(new_posts)), "verbose")
    uncommented = []
    for post in new_posts:
        if post.num_comments < 2 and \
                post.created_utc > (time.time() - (48 * 60 * 60)):
            uncommented.append(post)
    if uncommented:
        uncommented.reverse()  # Reverse so list is old to new
        post_count = len(uncommented)
        spammy = False
        if post_count > 2:
            spammy = True
        if spammy:
            Willie.reply(u"There are a few, I'll send them in pm.")
        for post in uncommented:
            if post.num_comments == 0:
                num_com = u"There are no comments"
            else:
                num_com = u"There is only 1 comment"
            if post.author.name.lower()[len(post.author.name) - 1] == u's':
                apos = u"'"
            else:
                apos = u"'s"
            c_date = datetime.utcfromtimestamp(post.created_utc)
            f_date = c_date.strftime(u'%b %d')
            if spammy:
                Willie.msg(
                    trigger.nick,
                    u'%s on %s%s post (%s) on %s entitled "%s"' % (
                        num_com,
                        colorize(post.author.name, [u'purple']),
                        apos,
                        post.short_link,
                        f_date,
                        colorize(post.title, [u'navy'])
                    )
                )
            else:
                Willie.reply(
                    u'%s on %s%s post (%s) on %s entitled "%s"' % (
                        num_com,
                        colorize(post.author.name, [u'purple']),
                        apos,
                        post.short_link,
                        f_date,
                        colorize(post.title, [u'navy'])
                    )
                )
    else:
        Willie.reply(u"I don't see any lonely posts. There could still be "
                     u"posts that need critiquing, though: "
                     u"http://mlpdrawingschool.reddit.com/"
                     )


if __name__ == "__main__":
    print __doc__.strip()
