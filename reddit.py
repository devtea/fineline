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
from pprint import pprint
from urllib2 import HTTPError
from socket import timeout

import praw
import praw.errors
from praw.errors import InvalidUser, InvalidSubreddit
from requests import HTTPError

from colors import *
from willie import web

_url='(reddit\.com|redd\.it)'
_partial = r'((^|[^A-Za-z0-9])/(r|u(ser)?)/[^/\s\.]{3,20})'
_ignore=['hushmachine','tmoister1']
_TIMEOUT=20
_UA='FineLine IRC bot 0.1 by /u/tdreyer1'
_timout_message = 'Sorry, reddit is unavailable right now.'
_bad_reddit_msg = "That doesn't seem to exist on reddit."
_bad_user_msg = "That user doesn't seem to exist."

#Use multiprocess handler for multiple bots on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)

def reddit_post(Willie, trigger):
    """Posts basic info on reddit links"""
    #If you change these, you're going to have to update others too
    user='/u(ser)?/[^/\s)]{3,20}'
    subm=('%s((/r/[^/\s]{3,20}/comments/[^/\s]{3,}(/[^/\s)]{3,})?/?)|'
            '(/[^/\s)]{4,}/?))') % _url
    cmnt='%s(/r/[^/\s]{3,20}/comments/[^/\s]{3,}/[^/\s]{3,}/[^/\s?]{3,}/?)(?:\?context=\d{,2})?' % _url
    subr='%s/r/[^/\s)]+/?([\s.!?]|$)' % _url

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
        Willie.debug('reddit.py:date_aniv', aniv, 'verbose')

        def set_date(year, month, day):
            try:
                date = datetime.strptime(
                        '%i %i %i' % (year, month, day),
                        '%Y %m %d'
                        )
            except ValueError:
                # Catch leap days and set them appropriately on off years
                date = datetime.strptime(
                        '%i %i %i' % (year, month, day-1),
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
            #Assume neither year is leap year
            if m1 < m2 or (m1 == m2 and d1 < d2):
                y1=y2+1
            else:
                y1=y2
            aniv = set_date(y1, m1, d1)
            day = set_date(y2, m2, d2)
            diff = aniv-day  #  diff is timedelta object
            diff = int(diff.total_seconds()/(24*60*60))
        return diff

    # User Section
    if re.match('.*?%s' % user, trigger.bytes):
        Willie.debug("reddit:reddit_post", "URL is user", "verbose")
        full_url = re.search(
                r'(https?://)?(www\.)?%s?%s' % (_url, user),
                trigger.bytes
                ).group(0)
        if re.match('^/u', full_url):
            full_url = 'http://reddit.com%s' % full_url
        Willie.debug("reddit:reddit_post", 'URL is %s' % full_url, "verbose")
        # If you change these, you're going to have to update others too
        username = re.split(
                "reddit\.com/u(ser)?/",
                full_url
                )[2].strip('/')
        Willie.debug(
                "reddit:reddit_post",
                'Username is %s' % username,
                "verbose"
                )
        try:
            redditor = rc.get_redditor(username)
        except (InvalidUser):
            Willie.say(_bad_user_msg)
            return
        except (HTTPError, timeout):
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
            Willie.debug(
                    'reddit:reddit_post',
                    'Date parsing broke!',
                    'warning'
                    )
        Willie.say(
                u"User %s: Link Karma %i, Comment karma %i, %s" % (
                    colorize(redditor.name, ['purple']),
                    redditor.link_karma,
                    redditor.comment_karma, cake_message)
                )
    # Comment Section
    elif re.match('.*?%s' % cmnt, trigger.bytes):
        Willie.debug("reddit:reddit_post", "URL is comment", "verbose")
        full_url = ''.join(
                re.search(
                    r'(https?://)?(www\.)?%s' % cmnt,
                    trigger.bytes
                    ).groups())
        if not re.match('^http', full_url):
            full_url = 'http://%s' % full_url
        try:
            post = rc.get_submission(url=full_url)
        except (HTTPError, timeout):
                Willie.say(_timeout_message)
                return
        comment = post.comments[0]
        #Willie.debug("reddit:reddit_post", pprint(vars(post)), "verbose")
        ed = u''
        if comment.edited:
            ed = u'[edited] '
        nsfw = u''
        if post.over_18:
            nsfw =  u'%s post: ' % colorize(u"NSFW", ["red"], ["bold"])
        snippet = comment.body
        match = re.compile(r'\n')  # 2 lines to remove newline markup
        snippet = match.sub(u' ', snippet)
        snippet = trc(snippet, 15)
        Willie.say(
                u'Comment (↑%s|↓%s) by %s on %s%s — "%s"' % (
                    colorize(str(comment.ups), ['green']),
                    colorize(str(comment.downs), ['orange']),
                    colorize(comment.author.name, ['purple']),
                    nsfw,
                    trc(post.title, 15),
                    colorize(snippet.strip(), ['navy'])
                ))

    # Submission Section
    elif re.match('.*?%s' % subm, trigger.bytes):
        for n in _ignore:
            if re.match('%s.*?' % n, trigger.nick):
                return
        Willie.debug("reddit:reddit_post", "URL is submission", "verbose")
        full_url = re.search(
                r'(https?://)?(www\.)?%s' % subm,
                trigger.bytes
                ).group(0)
        if not re.match('^http', full_url):
            full_url = 'http://%s' % full_url
        Willie.debug(
                "reddit:reddit_post",
                "matched is %s" % full_url,
                "verbose"
                )
        if re.match('.*?redd\.it', full_url):
            Willie.debug("reddit:reddit_post", "URL is short", 'verbose')
            try:
                full_url=web.get_urllib_object(full_url, _TIMEOUT).geturl()
            except InvalidSubreddit:
                Willie.say(_bad_reddit_msg)
                return
            except (HTTPError, timeout):
                Willie.say(_timeout_message)
                return
        Willie.debug("reddit:reddit_post", 'URL is %s' %full_url, "verbose")
        try:
            page = rc.get_submission(full_url)
        except (HTTPError, timeout):
            Willie.say(_timeout_message)
            return
        page_self = u'Link'
        if page.is_self:
            page_self = u'Self'
        nsfw = u''
        if page.over_18:
            nsfw =  u'[%s] ' % colorize(u"NSFW", ["red"], ["bold"])
        Willie.say(
                u'%s%s post (↑%s|↓%s|%sc) by %s to %s — %s' % (
                        nsfw,
                        page_self,
                        colorize(str(page.ups), ['green']),
                        colorize(str(page.downs), ['orange']),
                        page.num_comments,
                        colorize(page.author.name, ['purple']),
                        page.subreddit.display_name,
                        colorize(page.title, ['navy'])
                        ))
    # Subreddit Section
    elif re.match('.*?%s' % subr, trigger.bytes):
        Willie.debug("reddit:reddit_post", "URL is subreddit", "verbose")
        full_url = re.search(
                r'(https?://)?(www\.)?%s' % subr,
                trigger.bytes
                ).group(0)
        Willie.debug("reddit:reddit_post", 'URL is %s' %full_url, "verbose")
        # TODO pull back and display appropriate information for this.
        # I honestly don't know what useful info there is here!
        sub_name = full_url.strip('/').rpartition('/')[2]
        Willie.debug("reddit:reddit_post", sub_name, "verbose")

        try:
            sub = rc.get_subreddit(sub_name)
        except InvalidSubreddit:
            #Willie.say(_bad_reddit_msg)
            return
        except (HTTPError, timeout):
            #Willie.say(_timeout_message)
            return
        #do stuff?
    # Invalid URL Section
    else:
        Willie.debug(
                "reddit:reddit_post",
                "Matched URL is invalid",
                "warning"
                )
        #fail silently
reddit_post.rule = '(.*?%s)|(.*?%s)' % (_url, _partial)


def mlpds_check(Willie, trigger):
    '''Checks for posts within the last 48h with fewer than 2 comments'''
    try:
        mlpds = rc.get_subreddit('MLPDrawingSchool')
    except InvalidSubreddit:
        Willie.say(_bad_reddit_msg)
        return
    except (HTTPError, timeout):
        Willie.say(_timeout_message)
        return
    new_posts = mlpds.get_new(limit=50)
    #Willie.debug("reddit:mlpds_check", pprint(dir(new_posts)), "verbose")
    uncommented = []
    for post in new_posts:
        if post.num_comments < 2 and post.created_utc > (time.time()-(48*60*60)):
            uncommented.append(post)
    if uncommented:
        uncommented.reverse()  # Reverse so list is old to new
        post_count = len(uncommented)
        spammy = False
        if post_count > 2:
            spammy = True
        if spammy:
            Willie.reply("There are a few, I'll send them in pm.")
        for post in uncommented:
            if post.num_comments == 0:
                num_com = "There are no comments"
            else:
                num_com = "There is only 1 comment"
            if post.author.name.lower()[len(post.author.name)-1] == u's':
                apos = "'"
            else:
                apos = "'s"
            c_date = datetime.utcfromtimestamp(post.created_utc)
            f_date = c_date.strftime('%b %d')
            if spammy:
                Willie.msg(
                        trigger.nick,
                        u'%s on %s%s post (%s) on %s entitled "%s"' % (
                            num_com,
                            colorize(post.author.name, ['purple']),
                            apos,
                            post.short_link,
                            f_date,
                            colorize(post.title, ['navy'])
                            )
                        )
            else:
                Willie.reply(
                        u'%s on %s%s post (%s) on %s entitled "%s"' % (
                            num_com,
                            colorize(post.author.name, ['purple']),
                            apos,
                            post.short_link,
                            f_date,
                            colorize(post.title, ['navy'])
                            )
                        )
    else:
        Willie.reply("I don't see any lonely posts. There could still be "
                "posts that need critiquing, though: "
                "http://mlpdrawingschool.reddit.com/")
mlpds_check.commands = ['queue','check','posts','que','crit','critique']
mlpds_check.rate = 120


if __name__ == "__main__":
    print __doc__.strip()
