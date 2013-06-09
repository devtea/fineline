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

import praw

from willie import web

#TODO PEP 8 Formatting
url='(reddit\.com|redd\.it)'
partial = r'((^|[^A-Za-z0-9])/(r|u(ser)?)/[^/\s\.]{3,20})'
_ignore=['hushmachine','tmoister1']
_TIMEOUT=20
_UA='FineLine IRC bot 0.1 by /u/tdreyer1'

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
C_UP = u'\x033'  # Green
C_DN = u'\x037'  # Orange
C_NSFW = u'\x034'  # Red
C_CNT = u'\x032'  # Blue
C_USER = u'\x036'  # Purple
C_CAKE = [
        u'\x031',
        u'\x034',
        u'\x032',
        u'\x033',
        u'\x035',
        u'\x036',
        u'\x037',
        u'\x0313'
        ]

#Use multiprocess handler for multiple bots on same server
praw_multi = praw.handlers.MultiprocessHandler()
rc = praw.Reddit(user_agent=_UA, handler=praw_multi)

def reddit_post(Willie, trigger):
    """Posts basic info on reddit links"""
    #If you change these, you're going to have to update others too
    user='/u(ser)?/[^/\s]{3,20}'
    subm=('%s((/r/[^/\s]{3,20}/comments/[^/\s]{3,}(/[^/\s]{3,})?/?)|'
            '(/[^/\s]{4,}/?))') % url
    cmnt='%s/r/[^/\s]{3,20}/comments/[^/\s]{3,}/[^/\s]{3,}/[^/\s]{3,}/?' % url
    subr='%s/r/[^/\s]+/?([\s.!?]|$)' % url

    def trc(message, length=5):
        m_list = message.split()
        short = message
        if len(m_list) > length:
            short = u' '.join([m_list[elem] for elem in range(length)])
            short = u'%s...' % short
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
                r'(https?://)?(www\.)?%s?%s' % (url, user),
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
            redditor_exists = True
            Willie.debug(
                    "reddit:reddit_post",
                    pprint(vars(redditor)),
                    "verbose"
                    )
        except:
            redditor_exists = False
        if redditor_exists:
            # Use created date to determine next cake day
            cakeday = datetime.utcfromtimestamp(redditor.created_utc)
            diff_days = date_aniv(cakeday)
            if diff_days == 0:
                cake_message = u'HAPPY CAKEDAY!'
                colorful_message = u''
                cnt = 0
                for c in cake_message:
                    colorful_message = colorful_message + C_CAKE[cnt %
                            len(C_CAKE)] + str(c)
                    cnt = cnt + 1
                cake_message= colorful_message + u'\x0f'
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
                    u"User %s%s%s: Link Karma %i, Comment karma %i, %s" % (
                        C_USER, redditor.name, C_RESET, redditor.link_karma,
                        redditor.comment_karma, cake_message)
                    )
        else:
            Willie.say(u"That user does not exist or reddit is being "
                "squirrely.")
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
        Willie.debug(
                "reddit:reddit_post",
                pprint(vars(comment.author)),
                "verbose"
                )
        if comment.edited:
            ed = u'[edited] '
        else:
            ed = u''
        if post.over_18:
            nsfw =  u'%sNSFW%s post: ' % (C_NSFW, C_RESET)
        else:
            nsfw = u''
        snippet = comment.body
        match = re.compile(r'\n')  # 2 lines to remove newline markup
        snippet = match.sub(u' ', snippet)
        snippet = trc(snippet, 15)
        Willie.say(
                u'Comment (%s↑%i%s|%s↓%i%s) ' % (C_UP, comment.ups, C_RESET,
                    C_DN, comment.downs, C_RESET) +
                u'by %s%s%s ' % (C_USER, comment.author.name, C_RESET) +
                u'on %s%s — "' % (nsfw, trc(post.title, 15)) +
                u'%s%s%s"' % (C_CNT, snippet.strip(), C_RESET)
                )
        Willie.debug("", full_url, "verbose")

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
                nsfw =  u'[%sNSFW%s] ' % (C_NSFW, C_RESET)
            else:
                nsfw = u''

            Willie.say(
                    u'%s' % nsfw +
                    u'%s ' % page_self +
                    u'post (%s↑%i%s|%s↓%i%s|' % (C_UP, page.ups, C_RESET,
                        C_DN, page.downs, C_RESET) +
                    u'%ic) ' % page.num_comments +
                    u'by %s%s%s ' % (C_USER, page.author.name, C_RESET) +
                    u'to %s — ' % page.subreddit.display_name +
                    u'%s%s%s' % (C_CNT, page.title, C_RESET)
                    )
        else:
            Willie.say(u"That page does not exist or reddit is being "
                "squirrely.")
    # Subreddit Section
    elif re.match('.*?%s' % subr, trigger.bytes):
        # TODO add support for bare /r/subreddit 'links'
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
    # Invalid URL Section
    else:
        Willie.debug(
                "reddit:reddit_post",
                "Matched URL is invalid",
                "warning"
                )
        #fail silently
reddit_post.rule = '(.*?%s)|(.*?%s)' % (url, partial)


def mlpds_check(Willie, trigger):
    mlpds = rc.get_subreddit('MLPDrawingSchool')
    new_posts = mlpds.get_new(limit=50)
    Willie.debug("reddit:mlpds_check", pprint(dir(new_posts)), "verbose")
    uncommented = []
    for post in new_posts:
        #Willie.debug("reddit:mlpds_check", pprint(vars(new_cmnts)), "verbose")
        #Willie.debug("reddit:mlpds_check", pprint(vars(post)), "verbose")
        #Willie.debug("reddit:mlpds_check", pprint(dir(post)), "verbose")
        if post.num_comments < 2 and post.created_utc > (time.time()-(48*60*60)):
            uncommented.append(post)
    if uncommented:
        uncommented.reverse()  # Reverse so list is old to new
        post_count = len(uncommented)
        spammy = False
        if post_count > 2:
            spammy = True
        #Send private message
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
                        u'%s on %s%s post (%s) on %s entitled %s"%s"%s' % (
                            num_com, post.author.name, apos, post.short_link,
                            f_date, C_CNT, post.title, C_RESET
                            )
                        )
            else:
                Willie.reply(
                        u'%s on %s%s post (%s) on %s entitled %s"%s"%s' % (
                            num_com, post.author.name, apos, post.short_link,
                            f_date, C_CNT, post.title, C_RESET
                            )
                        )
    else:
        Willie.reply("I don't see any lonely posts. There could still be "
                "posts that need critiquing, though: "
                "http://mlpdrawingschool.reddit.com/")

mlpds_check.commands = ['check']


if __name__ == "__main__":
    print __doc__.strip()
