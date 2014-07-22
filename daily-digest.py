"""
daily-digest.py - A Willie module that summarizes and displays images posted in the last day
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import re
import threading
import time
import traceback
import urlparse
import urllib2
from pprint import pprint as pp
from HTMLParser import HTMLParser
from string import Template

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

EXPIRATION = 5 * 24 * 60 * 60  # 24 hour expiration, 5 day for testing
IGNORE = ['hushmachine', 'hushbot', 'hushrobot']


class ImageParser(HTMLParser):
    def get_img(self):
        try:
            return self.img
        except:
            return None


class DAParser(ImageParser):
    def handle_starttag(self, tag, attrs):
        # Easiest way to grab an image from deviant art is to parse the page
        # and pull out the (hopefully) only img tag with a class of
        # 'dev-content-full'
        if tag == 'img' and attrs:
            # Attrs are a list of tuples, (name, value)
            d = {}
            for attr in attrs:
                d[attr[0]] = attr[1]
            if d and 'class' in d and d['class'] == 'dev-content-full':
                self.img = d['src']


class ImgurParser(ImageParser):
    def handle_starttag(self, tag, attrs):
        # Imgur pages will either have a single link with a src attribute, or a
        # buch of links with a data-src attribute
        if tag == 'img' and attrs:
            # Attrs are a list of tuples, (name, value)
            d = {}
            for attr in attrs:
                d[attr[0]] = attr[1]
                if d and 'src' in d and d['src'].startswith('//i.imgur'):
                    self.img = 'http://%s' % d['src'].strip('/')


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
        bot.memory['digest'] = {}
    if 'digest' not in bot.memory['digest']:
        bot.memory['digest']['digest'] = []
    if 'digest_context' not in bot.memory:
        bot.memory['digest']['context'] = []
    if 'digest_lock' not in bot.memory:
        bot.memory['digest']['lock'] = threading.Lock()
    if 'digest_context_lock' not in bot.memory:
        bot.memory['digest']['context_lock'] = threading.Lock()

    # Load config values
    bot.memory['digest']['template'] = bot.config.dailydigest.template
    bot.memory['digest']['destination'] = bot.config.dailydigest.destination
    bot.memory['digest']['url'] = bot.config.dailydigest.url
    with open(bot.memory['digest']['template'], 'r') as f:
        try:
            bot.memory['digest']['templatehtml'] = Template(f.read())
        except:
            bot.debug(__file__, log.format(u'Unable to load template.'), u'always')
            raise

    with bot.memory['digest']['lock']:
        bot.memory['digest']['some_dictionary'] = {}

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
    # Image services to Support
    # Imgur
    # Sta.sh
    # Deviant Art / fav.me
    # 500px
    # flickr
    FILELIST = ['png', 'jpg', 'jpeg', 'tiff', 'gif', 'bmp']
    _dom_map = {
        'deviantart.net': re.compile('\S+\.deviantart\.net'),
        'deviantart.com': re.compile('\S+\.deviantart\.com'),
        'imgur.com': re.compile('i\.imgur\.com')
    }
    domains = {
        'deviantart.net': (lambda url: deviantart(url)),
        'deviantart.com': (lambda url: deviantart(url)),
        'i.imgur.com': (lambda url: imgur(url)),
        'imgur.com': (lambda url: imgur(url)),
        'derpicdn.net': (lambda url: derpibooru(url)),
        'static1.e621.net': (lambda url: e621(url)),
        'e621.net': (lambda url: e621(url))
    }

    def deviantart(url):
        parser = DAParser()
        try:
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            parser.feed(html)
        except:
            print(u'[daily-digest.py] Unhandled exception in the DA parser.')
            print(traceback.format_exc())
            return None
        return parser.get_img()

    def imgur(url):
        # Imgur has a lot of shit urls, filter them first before trying to
        # parse the html.
        if re.search('user|\.com/?$|//[^\.\W]{2,}\.imgur.com', url, re.I):
            return None

        parser = ImgurParser()
        try:
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            parser.feed(html)
        except:
            print(u'[daily-digest.py] Unhandled exception in the imgur parser.')
            print(traceback.format_exc())
            return None
        img = parser.get_img()
        if img:
            # If we got an image back, return it
            return img
        else:
            # Else return the original URL for album embedding
            return url

    def derpibooru(url):
        return url

    def e621(url):
        return url

    bot.debug(__file__, log.format("Filtering URL %s" % url), 'verbose')

    parsed_url = urlparse.urlparse(url)
    domain = '{uri.netloc}/'.format(uri=parsed_url).strip('/')
    # Regex replacements for certain domains
    bot.debug(__file__, log.format("Unprocessed domain is: %s" % domain), 'verbose')
    for r in _dom_map:
        domain = _dom_map[r].sub(r, domain)
    bot.debug(__file__, log.format("Processed domain is: %s" % domain), 'verbose')

    # TODO Are there urls with shit after the file name? eg.
    # http://example.net/image.png?shit=stuffs
    if url.split('.')[-1] in FILELIST:
        bot.debug(__file__, log.format("Url %s appears a raw image link." % url), 'verbose')
        return {'url': url, 'service': domain}

    # Try to get url function for specific domain
    try:
        check = domains[domain]
    except KeyError:
        bot.debug(__file__, log.format("Domain %s not found." % domain), 'verbose')
        return None

    # If we got a check function, use that to return the image url
    # TODO try except
    return {'url': check(url), 'service': domain}

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

url = re.compile(r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?]))''')
re_nsfw = re.compile(r'(?i)NSFW|suggestive|nude|questionable|explicit|porn|clop')


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
    with bot.memory['digest']['context_lock']:
        local_context = [i for i in bot.memory['digest']['context']]

    for u in matches:
        original = u
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
        if not u['url']:
            return
        t = {
            'time': now,
            'message': trigger.bytes,
            'author': nicks.NickPlus(trigger.nick, trigger.host),
            'nsfw': nsfw,
            'url': original,
            'image': u['url'],
            'service': u['service'],
            'channel': trigger.sender,
            'reported': False
            }
        with bot.memory['digest']['lock']:
            bot.memory['digest']['digest'].append(t)

        bot.debug(__file__, log.format(pp(t)), 'verbose')


@commands('digest_clear')
def digest_clear(bot, trigger):
    if not trigger.owner:
        return
    with bot.memory['digest']['lock']:
        bot.memory['digest']['digest'] = []
    bot.reply(u'Cleared.')


@commands('digest_dump')
def digest_dump(bot, trigger):
    if not trigger.owner:
        return
    with bot.memory['digest']['lock']:
        bot.reply(u'Dumping digest to logs.')
        bot.debug(__file__, log.format('=' * 20), 'always')
        bot.debug(__file__, log.format('time is %s' % time.time()), 'always')
        for i in bot.memory['digest']['digest']:
            bot.debug(__file__, log.format(pp(i)), 'always')
        bot.debug(__file__, log.format('=' * 20), 'always')


@interval(3600)
def clean_links(bot):
    '''Remove old links from bot memory'''
    with bot.memory['digest']['lock']:
        bot.memory['digest']['digest'] = [i for i in bot.memory['digest']['digest'] if i['time'] > time.time() - EXPIRATION]


@rule('.*')
def context(bot, trigger):
    '''Function to keep a running context of messages.'''
    with bot.memory['digest']['context_lock']:
        bot.memory['digest']['context'].append((trigger.sender, trigger.bytes))

        # Trim list to keep it contextual
        if len(bot.memory['digest']['context']) > 20:
            bot.memory['digest']['context'].pop(0)


@commands('context_clear')
def context_clear(bot, trigger):
    if not trigger.owner:
        return
    with bot.memory['digest']['context_lock']:
        bot.memory['digest']['context'] = []
    bot.reply(u'Cleared.')


@commands('digest_url_dump')
def url_dump(bot, trigger):
    if not trigger.owner:
        return
    with bot.memory['digest']['lock']:
        bot.reply(u'Dumping digest urls to logs.')
        bot.debug(__file__, log.format('=' * 20), 'always')
        for i in bot.memory['digest']['digest']:
            bot.debug(__file__, log.format(i['image']), 'always')
        bot.debug(__file__, log.format('=' * 20), 'always')


@interval(60)
def build_regularly(bot):
    build_html(bot, None)


@commands('digest_build_html')
def build_html(bot, trigger):
    bot.debug(__file__, log.format(log.format(bot.memory['digest']['destination'])), 'verbose')
    try:
        with open(bot.memory['digest']['destination'], 'r') as f:
            previous_html = ''.join(f.readlines())
    except IOError:
        previous_html = ''
        bot.debug(__file__, log.format(u'IO error grabbing "list_main_dest_path" file contents. File may not exist yet'), 'warning')

    # Generate HTML
    simple_header = '<title>Image digest</title>\n        <style type=\'text/css\'>body \{margin:0\}</style>\n'
    simple_img = '<img src="%s">'
    html = bot.memory['digest']['templatehtml'].substitute(
        body='\n'.join(
            [simple_img % i['image'] for i in bot.memory['digest']['digest']]
            ),
        head = simple_header
    )
    if previous_html != html:
        with open(bot.memory['digest']['destination'], 'w') as f:
            f.write(html)
    else:
        bot.debug(__file__, log.format(u'No chage in digest html file, skipping.'), u'verbose')


if __name__ == "__main__":
    print(__doc__.strip())
