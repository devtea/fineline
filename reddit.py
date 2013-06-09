# coding=utf8
"""
reddit.py - A simple Willie module that provides reddit functionality
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import praw
import re
from datetime import datetime
from pprint import pprint
from willie import web
from urllib2 import HTTPError

url='(reddit\.com|redd\.it)'
IGNORE=['hushmachine','tmoister1']
TIME_OUT=20
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
C_UP = u'\x032'  # Blue
C_DN = u'\x037'  # Orange
C_NSFW = u'\x034'  # Red
C_CNT = u'\x032'  # Blue
C_USER = u'\x036'  # Purple


#Use multiprocess handler for multiple bots on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent='FineLine IRC bot 0.1 by /u/tdreyer1', handler=praw_multi)

#TODO Add message sending ability
#TODO Add support for /u/username and /r/subreddit
#TODO PEP 8 Formatting
#TODO add consistent management of color formatting


def reddit_post(Willie, trigger):
    """Posts basic info on reddit links"""
    #If you change these, you're going to have to update others too
    user='%s/u(ser)?/[^/\s]{3,20}' % url
    subm='%s((/r/[^/\s]{3,20}/comments/[^/\s]{3,}(/[^/\s]{3,})?/?)|(/[^/\s]{4,}/?))' % url
    cmnt='%s/r/[^/\s]{3,20}/comments/[^/\s]{3,}/[^/\s]{3,}/[^/\s]{3,}/?' % url
    subr='%s/r/[^/\s]+/?([\s.!?]|$)' % url

    def date_aniv(aniv, day=datetime.now()):
        Willie.debug('reddit.py:date_aniv', aniv, 'verbose')
        def set_date(year, month, day):
            try:
                date = datetime.strptime('%i %i %i' % (year, month, day), '%Y %m %d')
            except ValueError:
                # Catch leap days and set them appropriately on off years
                date = datetime.strptime('%i %i %i' % (year, month, day-1), '%Y %m %d')
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
                r'(https?://)?(www\.)?%s' % user,
                trigger.bytes
                ).group(0)
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
            redditor_exists = True
            Willie.debug("reddit:reddit_post", pprint(vars(redditor)), "verbose")
        except:
            redditor_exists = False
        if redditor_exists:
            # Use created date to determine next cake day
            cakeday = datetime.utcfromtimestamp(redditor.created_utc)  # unix date
            diff_days = date_aniv(cakeday)
            if diff_days == 0:
                cake_message = u'HAPPY CAKEDAY!'
            elif diff_days > 0:
                cake_message = u"Cakeday in %i day(s)" % diff_days
            else:
                # oh shit, something went wrong
                cake_message = u""
                Willie.debug('reddit:reddit_post', 'Date parsing broke!', 'warning')
            Willie.say(
                    u"%s%s%s: Link Karma %i, Comment karma %i, %s" % (C_USER,
                        redditor.name, C_RESET, redditor.link_karma,
                        redditor.comment_karma, cake_message)
                    )
        else:
            Willie.say(u"That user does not exist or reddit is being squirrely.")
    # Comment Section
    elif re.match('.*?%s' % cmnt, trigger.bytes):
        Willie.debug("reddit:reddit_post", "URL is comment", "verbose")
        full_url = re.search(
                r'(https?://)?(www\.)?%s' % cmnt,
                trigger.bytes
                ).group(0)
        if not re.match('^http', full_url):
            full_url = 'http://%s' % full_url
        post = rc.get_submission(url=full_url)
        comment = post.comments[0]
        Willie.debug("reddit:reddit_post", pprint(vars(post)), "verbose")
        Willie.debug("reddit:reddit_post", pprint(vars(comment)), "verbose")
        Willie.debug("reddit:reddit_post", pprint(vars(comment.author)), "verbose")
        if comment.edited:
            ed = u'[edited] '
        else:
            ed = u''
        if post.over_18:
            nsfw =  u'%sNSFW%s post: ' % (C_NSFW, C_RESET)
        else:
            nsfw = u''
        snippet = comment.body
        match = re.compile(r'\n')
        snippet = match.sub(u' ', snippet)
        snippet_list = snippet.split()
        if len(snippet_list) > 15:
            snippet = ' '.join([snippet_list[elem] for elem in range(15)])
            snippet = '%s...' % snippet
        Willie.say(
                u'(%s↑%i%s|%s↓%i%s) ' % (C_UP, comment.ups, C_RESET, C_DN, comment.downs, C_RESET) +
                u'Comment by %s%s%s ' % (C_USER, comment.author.name, C_RESET) +
                u'on %s%s — "' % (nsfw, post.title) +
                u'%s%s%s"' % (C_CNT, snippet.strip(), C_RESET)
                )
        Willie.debug("", full_url, "verbose")

    # Submission Section
    elif re.match('.*?%s' % subm, trigger.bytes):
        for n in IGNORE:
            if re.match('%s.*?' % n, trigger.nick):
                return
        Willie.debug("reddit:reddit_post", "URL is submission", "verbose")
        full_url = re.search(
                r'(https?://)?(www\.)?%s' % subm,
                trigger.bytes
                ).group(0)
        if not re.match('^http', full_url):
            full_url = 'http://%s' % full_url
        Willie.debug("reddit:reddit_post", "matched is %s" % full_url, "verbose")
        if re.match('.*?redd\.it', full_url):
            Willie.debug("reddit:reddit_post", "URL is short", 'verbose')
            try:
                full_url=web.get_urllib_object(full_url, TIME_OUT).geturl()
            except HTTPError:
                Willie.debug(
                        "reddit:reddit_post",
                        "URL fetching timed out",
                        'verbose'
                        )
        Willie.debug("reddit:reddit_post", 'URL is %s' %full_url, "verbose")
        try:
            page = rc.get_submission(full_url)
        except:
            page_exists = False
        else:
            page_exists = True
            Willie.debug("reddit:reddit_post", pprint(vars(page)), "verbose")
        if page_exists:
            if page.is_self:
                page_self = u'Self'
            else:
                page_self = u'Link'
            if page.over_18:
                nsfw =  u'%sNSFW%s ' % (C_NSFW, C_RESET)
            else:
                nsfw = u''

            Willie.say(
                    u'[%s] ' % page_self +
                    u'%s' % nsfw +
                    u'Post by %s%s%s ' % (C_USER, page.author.name, C_RESET) +
                    u'to %s ' % page.subreddit.display_name +
                    u'(%s↑%i%s|%s↓%i%s|' % (C_UP, page.ups, C_RESET, C_DN, page.downs, C_RESET) +
                    u'%ic) — ' % page.num_comments +
                    u'%s%s%s' % (C_CNT, page.title, C_RESET)
                    )
        else:
            Willie.say(u"That page does not exist or reddit is being squirrely.")
    # Subreddit Section
    elif re.match('.*?%s' % subr, trigger.bytes):
        Willie.debug("reddit:reddit_post", "URL is subreddit", "verbose")
        full_url = re.search(
                r'(https?://)?(www\.)?%s' % subr,
                trigger.bytes
                ).group(0)
        Willie.debug("reddit:reddit_post", 'URL is %s' %full_url, "verbose")
        # TODO pull back and display appropriate information for each.
        # I honestly don't know what useful info there is here!
        sub_name = full_url.strip('/').rpartition('/')[2]
        Willie.debug("reddit:reddit_post", sub_name, "verbose")

        try:
            sub = rc.get_subreddit(sub_name)
        except:
            sub_exists = False
        else:
            sub_exists = True
            Willie.debug("reddit:reddit_post", pprint(vars(sub)), "verbose")
        if sub_exists:
            #do stuff?
            pass
        else:
            #do other stuff
            pass
        #Willie.say(r'Hello World!')
    # Invalid URL Section
    else:
        Willie.debug("reddit:reddit_post", "Matched URL is invalid", "warning")
        #fail silently

reddit_post.rule = '.*?%s' % url



if __name__ == "__main__":
    print __doc__.strip()
