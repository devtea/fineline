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

url='reddit\.com'

rc = praw.Reddit(user_agent='FineLine IRC bot 0.1 by /u/tdreyer1')
#TODO Add message sending ability
#TODO Add parsing for shortlinks
#TODO Add support for /u/username and /r/subreddit


def reddit_post(Willie, trigger):
    """Posts basic info on reddit links"""
    #If you change these, you're going to have to update others too
    user='%s/u(ser)?/[^/\s]{3,}' % url
    subm='%s/r/[^/\s]+/comments/[^/\s]{3,}/[^/\s]{3,}/?' % url
    subr='%s/r/[^/\s]+/?([\s.!?]|$)' % url

    def date_aniv(aniv, day=datetime.now()):
        def set_date(year, month, day):
            try:
                date = datetime.strptime('%i %i %i' % (year, month, day), '%Y %m %d')
            except ValueError:
                # Catch leap days and set them appropriately on off years
                date = datetime.strptime('%i %i %i' % (year, month, day-1), '%Y %m %d')
            return date

        y1, m1, d1 = aniv.strftime('%Y %m %d').split()
        y2, m2, d2 = day.strftime('%Y %m %d').split()

        # Ugly int casting
        y1=int(y1)
        y2=int(y2)

        m1=int(m1)
        m2=int(m2)

        d1=int(d1)
        d2=int(d2)
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
        except:
            redditor = False
        if not redditor:
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
            Willie.say(
                    u"%s: Link Karma %i, Comment karma %i, %s" % (redditor.name,
                        redditor.link_karma, redditor.comment_karma, cake_message)
                    )
        else:
            Willie.say(u"That user does not exist or reddit is being squirrely.")
    # Submission Section
    elif re.match('.*?%s' % subm, trigger.bytes):
        Willie.debug("reddit:reddit_post", "URL is submission", "verbose")
        full_url = re.search(
                r'(https?://)?(www\.)?%s' % subm,
                trigger.bytes
                ).group(0)
        Willie.debug("reddit:reddit_post", 'URL is %s' %full_url, "verbose")
        # TODO pull back and display appropriate information for each.
        try:
            page = rc.get_submission(full_url)
            page_exists = True
            Willie.debug("reddit:reddit_post", pprint(vars(page)), "verbose")
        except:
            page_exists = False
        if page_exists:
        #[self] NSFW Post by UserName to Subreddit (9999^|200v|22c) - Title is really
        #       long I guess
            if page.is_self:
                page_self = u'Self'
            else:
                page_self = u'Link'
            if page.over_18:
                nsfw =  u'\x034NSFW\x0f '  # \x034 is red, \x0f resets
            else:
                nsfw = u''

            Willie.say(
                    u'[%s] ' % page_self +
                    u'%s' % nsfw +
                    u'Post by %s ' % page.author.name +
                    u'to %s ' % page.subreddit.display_name +
                    u'(%i↑|%i↓|' % (page.ups, page.downs) +
                    u'%ic) — ' % page.num_comments +
                    u'%s' % page.title
                    )
            #for line in title_lines:
                #say extra lines!
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
        #Willie.say(r'Hello World!')
    # Invalid URL Section
    else:
        Willie.debug("reddit:reddit_post", "URL is invalid", "verbose")
        #fail silently

reddit_post.rule = '.*?%s' % url



if __name__ == "__main__":
    print __doc__.strip()
