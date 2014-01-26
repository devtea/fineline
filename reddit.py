# coding=utf8
"""
reddit.py - A simple Willie module that provides reddit functionality
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

Depends on PRAW: https://github.com/praw-dev/praw
"""
import re
from datetime import datetime
#from urllib2 import HTTPError
from socket import timeout
import imp
import sys

import praw
import praw.errors
from praw.errors import InvalidUser, InvalidSubreddit
from requests import HTTPError

from willie.tools import Nick
from willie.module import commands, rule

_url = u'(reddit\.com|redd\.it)'
_partial = ur'((^|[^A-Za-z0-9])/(r|u(ser)?)/[^/\s\.]{3,20})'
_ignore = [u'hushmachine', u'tmoister1']
_TIMEOUT = 20
_UA = u'FineLine IRC bot 0.1 by /u/tdreyer1'
_timeout_message = u'Sorry, reddit is unavailable right now.'
_error_msg = u"That doesn't exist, or reddit is being squirrely."
_bad_reddit_msg = u"That doesn't seem to exist on reddit."
_bad_user_msg = u"That user doesn't seem to exist."
_ignore = [Nick(r'hushmachine.*'), Nick(r'tmoister1')]
_re_shorturl = re.compile('.*?redd\.it/(\w+)')

#Use multiprocess handler for multiple bots on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)

# Bot framework is stupid about importing, so we need to override so that
# the colors module is always available for import.
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

    trigger_nick = Nick(trigger.nick)
    for i in _ignore:
        if i == trigger_nick:
            return

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
            cake_message = colors.rainbow(u'HAPPY CAKEDAY!')
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
            colors.colorize(redditor.name, [u'purple']),
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
            nsfw = u'%s post: ' % colors.colorize(u"NSFW", [u"red"], [u"bold"])
        snippet = comment.body
        match = re.compile(ur'\n')  # 2 lines to remove newline markup
        snippet = match.sub(u' ', snippet)
        snippet = trc(snippet, 15)
        Willie.say(
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
        results = _re_shorturl.search(full_url)
        if results:
            Willie.debug(u"reddit:reddit_post", u"URL is short", u'verbose')
            use_id = True
            post_id = results.groups()[0]
            '''
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
            '''
        if use_id:
            pass
        else:
            Willie.debug(u"reddit:reddit_post",
                         u'URL is %s' % full_url,
                         u"verbose"
                         )
        try:
            if use_id:
                page = rc.get_submission(submission_id=post_id)
            else:
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
            nsfw = u'[%s] ' % colors.colorize(u"NSFW", [u"red"], [u"bold"])
        pname = u'[deleted]'
        if page.author:
            pname = colors.colorize(page.author.name, [u'purple'])
        Willie.say(
            u'%s%s post (↑%s|↓%s|%sc) by %s to %s — %s' % (
                nsfw,
                page_self,
                colors.colorize(str(page.ups), [u'green']),
                colors.colorize(str(page.downs), [u'orange']),
                page.num_comments,
                pname,
                page.subreddit.display_name,
                colors.colorize(page.title, [u'blue'])
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
            #sub = rc.get_subreddit(sub_name)
            pass
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


if __name__ == "__main__":
    print __doc__.strip()
