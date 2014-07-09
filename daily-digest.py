"""
daily-digest.py - A Willie module that summarizes and displays images posted in the last day
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

# import stuff
import re
import threading
import time
from pprint import pprint as pp

from willie.module import commands, rule, interval

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        print("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', ['./.willie/modules/'])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()
try:
    import nicks
except:
    import imp
    import sys
    try:
        print("trying manual import of nicks")
        fp, pathname, description = imp.find_module('nicks', ['./.willie/modules/'])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()

EXPIRATION = 24 * 60 * 60  # 24 hour expiration
IGNORE = ['hushmachine', 'hushbot', 'hushrobot']


def configure(config):
    '''
    [ daily-digest ]
    -----------
    | option1 | False | Option one, defaults to false |
    | option2 | http,ftp,sftp | option two, a list of things |
    '''
    if config.option('Configure this module?', False):
        config.add_option('template', 'option1', "Do the thing?", default=False)
        config.add_list('template', 'option2', "Which things?")


def setup(bot):
    if 'digest' not in bot.memory:
        bot.memory['digest'] = []
    if 'digest_context' not in bot.memory:
        bot.memory['digest_context'] = []

    if 'digest_lock' not in bot.memory:
        bot.memory['digest_lock'] = threading.Lock()
    if 'digest_context_lock' not in bot.memory:
        bot.memory['digest_context_lock'] = threading.Lock()
    with bot.memory['digest_lock']:
        bot.memory['some_dictionary'] = {}

        db = bot.db.connect()
        cur = db.cursor()
        query = None
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS template
                           (name text, score int)''')
            db.commit()
            cur.execute('SELECT name, score FROM template')
            query = cur.fetchall()
        finally:
            cur.close()
            db.close()
        if query:
            for t, s in query:
                # Handle returnedquery
                pass


@commands(u'dd', u'dailydigest', u'digest')
def template(bot, trigger):
    """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis sodales. """
    bot.debug(__file__, log.format('Log message'), 'verbose')
    pass


def image_filter(bot, url):
    '''Filter URLs for known image hosting services and raw image links'''
    """
    _re_imgur = re.compile('imgur\.com/([^\s]+?)\.\S{3}')
    _re_deviantart = re.compile('/\w+/\w+/\w+/\w+-(\w+)\.\w{3,4}')
    domains = {
        'deviantart.net': (lambda url: deviantart(url)),
        'i.imgur.com': (lambda url: imgur(url)),
        'imgur.com': (lambda url: imgur(url))
    }

    def imgur(url):
        '''try:
            uid = _re_imgur.search(url).groups()[0]
        except:
            print u'[url.py] Unhandled exception in imgur parser.'
            return None
        return u'http://imgur.com/%s' % uid
        '''
        return None

    def deviantart(url):
        try:
            uid = _re_deviantart.search(url).groups()[0]
        except:
            print(u'[url.py] Unhandled exception in deviantart parser.')
            return None
        return 'http://fav.me/%s' % uid
"""
    # TODO
    service = 'Service Placeholder'
    return {'url': url, 'service': service}


url = re.compile(r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?]))''')
re_nsfw = re.compile(r'(?i)NSFW|suggestive|nude|explicit|porn|clop')


@rule(r'''(?i).*\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?]))''')
def url_watcher(bot, trigger):
    # Don't record stuff from private messages
    if not trigger.sender.startswith('#') or trigger.nick in IGNORE:
        return

    now = time.time()

    try:
        matches = [i[0] for i in url.findall(trigger.bytes)]
    except IndexError:
        bot.debug(__file__, log.format('Error finding all URLs in message - No urls found!'), 'warning')
        bot.debug(__file__, log.format('Message was: %s' % trigger.bytes), 'warning')
        return

    time.sleep(10)  # Wait just a bit to grab post-link nsfw tagging context, but only once per message
    with bot.memory['digest_context_lock']:
        local_context = [i for i in bot.memory['digest_context']]

    for u in matches:
        # TODO Filter to include only direct image links and whitelisted image sites
        # to scrape. Probably can be combined with service checking.
        u = image_filter(bot, u)
        if not u:
            continue

        # NSFW checking. If the message line contains keywords, mark as NSFW. If
        # the context contains keywords, mark as unknown/maybe.
        nsfw = False
        if re_nsfw.search(trigger.bytes):
            nsfw = True
        else:
            for i in [x[1] for x in local_context if x[0] == trigger.sender]:
                if re_nsfw.search(i):
                    nsfw = None

        t = (
            now,
            u,
            {'message': trigger.bytes,
             'author': nicks.NickPlus(trigger.nick, trigger.host),
             'nsfw': nsfw,
             'service': 'service placeholder',
             'channel': trigger.sender,
             'reported': False
             })
        with bot.memory['digest_lock']:
            bot.memory['digest'].append(t)

        bot.debug(__file__, log.format(pp(t)), 'verbose')


@commands('digest_clear')
def digest_clear(bot, trigger):
    if not trigger.owner:
        return
    with bot.memory['digest_lock']:
        bot.memory['digest'] = []
    bot.reply(u'Cleared.')


@commands('digest_dump')
def digest_dump(bot, trigger):
    if not trigger.owner:
        return
    with bot.memory['digest_lock']:
        bot.reply(u'Dumping digest to logs.')
        bot.debug(__file__, log.format('=' * 20), 'always')
        bot.debug(__file__, log.format('time is %s' % time.time()), 'always')
        for i in bot.memory['digest']:
            bot.debug(__file__, log.format(pp(i)), 'always')
        bot.debug(__file__, log.format('=' * 20), 'always')


@interval(3600)
def clean_links(bot):
    '''Remove old links from bot memory'''
    with bot.memory['digest_lock']:
        bot.memory['digest'] = [i for i in bot.memory['digest'] if i[0] > time.time() - EXPIRATION]


@rule('.*')
def context(bot, trigger):
    '''Function to keep a running context of messages.'''
    with bot.memory['digest_context_lock']:
        bot.memory['digest_context'].append((trigger.sender, trigger.bytes))

        # Trim list to keep it contextual
        if len(bot.memory['digest_context']) > 20:
            bot.memory['digest_context'].pop(0)


@commands('context_clear')
def context_clear(bot, trigger):
    if not trigger.owner:
        return
    with bot.memory['digest_context_lock']:
        bot.memory['digest_context'] = []
    bot.reply(u'Cleared.')


if __name__ == "__main__":
    print(__doc__.strip())
