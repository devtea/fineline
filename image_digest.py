"""
image-digest.py - A Willie module that summarizes and displays images posted in the last day
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import hashlib
import json
import os.path
import re
import threading
import time
import types
import urlparse
import urllib2
from datetime import datetime
from pprint import pprint as pp
from HTMLParser import HTMLParser
from string import Template

from willie.logger import get_logger
from willie.module import commands, rule, interval, example

LOGGER = get_logger(__name__)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
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
        LOGGER.info(log.format("trying manual import of nicks"))
        fp, pathname, description = imp.find_module('nicks', [os.path.join('.', '.willie', 'modules')])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()
try:
    import util
except:
    import imp
    import sys
    try:
        LOGGER.info(log.format("trying manual import of util"))
        fp, pathname, description = imp.find_module('util', [os.path.join('.', '.willie', 'modules')])
        util = imp.load_source('util', pathname, fp)
        sys.modules['util'] = util
    finally:
        if fp:
            fp.close()

EXPIRATION = 3 * 24 * 60 * 60  # 24 hour expiration, longer for testing
BLACKLIST = ['i.4cdn.org']
_REMOVE_VOTES = 5
_VOTE_TIME = 5  # Time in minutes

_re_tumblr = re.compile(r'https?://\d+\.media\.tumblr\.com/[a-zA-Z0-9]+/tumblr_[a-zA-Z0-9_]+_\d+.[a-zA-Z]{,4}')

# Templates
_header_script = '''
    <script type="text/javascript" src="//code.jquery.com/jquery-2.1.1.min.js"></script>
    <script type="text/javascript">
    $(document).ready(function() {
    $('.nsfw').click(function() {
    $(this).toggleClass('shown');
        });
    });
    </script>
'''
_style = '''
    <style>
    div.img {
        margin: 5px;
        padding: 5px;
        border: 1px solid #000000;
        height: 550px;
        width: auto;
        float: left;
        text-align: center;
        word-wrap: break-word;
    }
    div.img img {
        display: inline;
        margin: 5px;
        border: 1px solid #ffffff;
        max-height: 350px;
    }
    div.img a:hover img {
        border:1px solid #0000ff;
    }
    div.img.nsfw a {
        visibility: hidden;
    }
    div.img.nsfw.shown a {
        visibility: visible;
    }
    div.desc {
        text-align: left;
        font-weight: normal;
        width: 300px;
        margin: 10px;
    }
    </style>
'''
_desc = '''
    <div class="desc">
        <p>
            <b>Date:</b> ${ftime}<br>
            <b>Channel:</b> ${channel}<br>
            <b>Message:</b> &lt;${author}&gt; ${message}<br>
            ${nsfw}
        </p>
    </div>
'''


_imgur_album = Template('<iframe class="imgur-album" width="100%" height="350" frameborder="0" src="${url}/embed?background=f2f2f2&text=1a1a1a&link=4e76c0"></iframe>')
_gfycat_iframe = Template('<iframe src="http://gfycat.com/ifr/${id}" frameborder="0" scrolling="no" height="350" width="600" style="-webkit-backface-visibility: hidden;-webkit-transform: scale(1);" ></iframe>')
_tinypic_gfycat_iframe = Template('<iframe src="http://gfycat.com/ifr/${id}" hash="${hash}" frameborder="0" scrolling="no" height="350" width="600" style="-webkit-backface-visibility: hidden;-webkit-transform: scale(1);" ></iframe>')
_img_div = Template('<div class="img">${img}${desc}</div>')
_img_div_nsfw = Template('<div class="img nsfw">${img}${desc}</div>')
_simple_img = Template('<a href="${orig}" target="_blank"><img src="${url}"></a>')
_desc_div = Template(_desc)


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
                self.img = re.sub('(deviantart.net/fs[0-9]+)/', '\g<1>/200H/', d['src'])
                try:
                    urllib2.urlopen(self.img)  # Basically just to test if the url throws a 404
                except urllib2.HTTPError:
                    self.img = d['src']  # if the small image doesn't exist (aka a gif) use full


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
                    self.img = u'http://%s' % d['src'].strip('/')


class TinyGrabParser(ImageParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'img' and attrs:
            # Attrs are a list of tuples, (name, value)
            d = {}
            for attr in attrs:
                d[attr[0]] = attr[1]
            if d and 'id' in d and d['id'] == 'thegrab':
                self.img = d['src']


class SteamParser(ImageParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'img' and attrs:
            # Attrs are a list of tuples, (name, value)
            d = {}
            for attr in attrs:
                d[attr[0]] = attr[1]
            if d and 'id' in d and d['id'] == 'ActualMedia':
                self.img = re.sub('\d+x\d+\.resizedimage', '0x200.resizedimage', d['src'])


class FivehpxParser(ImageParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'img' and attrs:
            # Attrs are a list of tuples, (name, value)
            d = {}
            for attr in attrs:
                d[attr[0]] = attr[1]
            if d and 'class' in d and d['class'] == 'the_photo':
                self.img = re.sub('(cdn\.500px\.org/\d+/\w+/)\d+\.', '\g<1>4.', d['src'])


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
    if 'context' not in bot.memory['digest']:
        bot.memory['digest']['context'] = []
    if 'lock' not in bot.memory['digest']:
        bot.memory['digest']['lock'] = threading.Lock()
    if 'context_lock' not in bot.memory['digest']:
        bot.memory['digest']['context_lock'] = threading.Lock()
    if 'to_remove' not in bot.memory['digest']:
        bot.memory['digest']['to_remove'] = None
    if 'count' not in bot.memory['digest']:
        bot.memory['digest']['count'] = 0

    # Load config values
    bot.memory['digest']['template'] = bot.config.dailydigest.template
    bot.memory['digest']['destination'] = "%sdaily-digest.html" % bot.config.general.hosted_path
    bot.memory['digest']['url'] = "%sdaily-digest.html" % bot.config.general.hosted_domain
    with open(bot.memory['digest']['template'], 'r') as f:
        try:
            bot.memory['digest']['templatehtml'] = Template(f.read().decode('utf-8', 'replace'))
        except:
            LOGGER.error(log.format(u'Unable to load template.'), exec_info=True)
            raise

    with bot.memory['digest']['lock']:
        # Temporary fix for database upgrade
        db = bot.db.connect()
        cur = db.cursor()
        query = None
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS digest
                        (time real,
                            message text,
                            author text,
                            nsfw integer,
                            url text,
                            image text,
                            service text,
                            channel text,
                            reported integer,
                            html text
                            )''')
            db.commit()
            cur.execute('SELECT time, message, author, nsfw, url, image, service, channel, reported, html FROM digest')
            query = cur.fetchall()
        finally:
            cur.close()
            db.close()
        if query:
            LOGGER.info(log.format('Reloading from database'))
            bot.memory['digest']['digest'] = []
            for t, m, a, n, u, i, s, c, r, h in query:
                item = {
                    'time': t,
                    'message': m,  # This is loaded from DB as unicode
                    'author': nicks.NickPlus(a.encode('utf-8', 'replace')),
                    'nsfw': parsebool(n),
                    'url': u,  # This is loaded from DB as unicode
                    'image': i,  # This is loaded from DB as unicode
                    'service': s,  # This is loaded from DB as unicode
                    'channel': c,  # This is loaded from DB as unicode
                    'html': h,  # This is loaded from DB as unicode
                    'reported': parsebool(r)
                }
                bot.memory['digest']['digest'].append(item)


def parsebool(b):
    '''Parses bools back and forth from ints for the database'''
    if isinstance(b, types.BooleanType):
        if b:
            return 1
        else:
            return 0
    elif b == 1:
        return True
    elif b == 0:
        return False
    return None


def imgur_get_medium(bot, url):
    try:
        if url.lower().endswith(u'.gif'):
            # Resized gifs don't animate'
            return url
        elif not re.search('(/[a-zA-Z0-9]{5,})[mls](.[a-zA-Z]{3,4})$', url):
            return re.sub('(/[a-zA-Z0-9]{5,})(.[a-zA-Z]{3,4})$', '\g<1>m\g<2>', url)
        else:
            return url
    except:
        LOGGER.error(log.format(u'Unhandled exception in the imgur medium url formatter.'), exec_info=True)
        return url


@commands(u'imagedigest', u'image-digest', u'id')
def template(bot, trigger):
    """Displays the url for the image digest page."""
    bot.say(u'The image digest page is at %s - Warning: NSFW posts are hidden but still download.' % bot.memory['digest']['url'])


def image_filter(bot, url):
    '''Filter URLs for known image hosting services and raw image links'''
    # TODO Image services to Support
    # misc boorus
    FILELIST = ['png', 'jpg', 'jpeg', 'tiff', 'gif', 'bmp', 'svg']
    _dom_map = {
        'deviantart.net': re.compile('\S+\.deviantart\.net'),
        'deviantart.com': re.compile('\S+\.deviantart\.com'),
        'imgur.com': re.compile('i\.imgur\.com'),
        'tinypic.com': re.compile('\S+\.tinypic\.com'),
        'tumblr.com': re.compile('\S+\.tumblr\.com')
    }
    domains = {
        'deviantart.net': (lambda url: deviantart(url)),
        'deviantart.com': (lambda url: deviantart(url)),
        'sta.sh': (lambda url: deviantart(url)),
        'fav.me': (lambda url: deviantart(url)),
        'dropbox.com': (lambda url: dropbox(url)),
        'www.dropbox.com': (lambda url: dropbox(url)),
        'i.imgur.com': (lambda url: imgur(url)),
        'm.imgur.com': (lambda url: imgur(url)),
        'imgur.com': (lambda url: imgur(url)),
        'derpiboo.ru': (lambda url: derpibooru(url)),
        'derpibooru.org': (lambda url: derpibooru(url)),
        'trixiebooru.org': (lambda url: derpibooru(url)),
        'derpicdn.net': (lambda url: derpibooru(url)),
        'cdn.derpiboo.ru': (lambda url: derpibooru(url)),
        'static1.e621.net': (lambda url: e621(url)),
        'e621.net': (lambda url: e621(url)),
        'gfycat.com': (lambda url: gfycat(url)),
        'www.gfycat.com': (lambda url: gfycat(url)),
        'grab.by': (lambda url: tinygrab(url)),
        'steamcommunity.com': (lambda url: steam(url)),
        '500px.com': (lambda url: fivehpx(url)),
        'www.flickr.com': (lambda url: flickr(url)),
        'flickr.com': (lambda url: flickr(url)),
        'tinypic.com': (lambda url: tinypic(url)),
        'tumblr.com': (lambda url: tumblr(url))
    }
    # Temporary list to specify which need to be preprocessed
    temp_preprocess = [
        'dropbox.com',
        'www.dropbox.com',
        'tinypic.com'
    ]

    def derpibooru(url):
        '''derpibooru provides an oembed option at derpiboo.ru/oembed.json'''
        try:
            content = urllib2.urlopen(u"http://derpiboo.ru/oembed.json?url=%s" % url)
            raw_json = content.read().decode('utf-8', 'replace')
            f_json = json.loads(raw_json)
            if 'thumbnail_url' in f_json:
                return {'url': f_json['thumbnail_url'], 'format': 'standard'}
            else:
                return None
        except:
            LOGGER.error(log.format(u'Unhandled exception in the derpibooru parser.'))
            return None

    def tumblr(url):
        try:
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            urls = _re_tumblr.findall(html)  # just a simple pattern search for certain urls
        except:
            LOGGER.error(log.format(u'Unhandled exception in the tumblr parser.'), exec_info=True)
            return None
        if urls:
            return {'url': urls[0], 'format': 'standard'}  # Just return the first, I guess?
        else:
            return None

    def tinygrab(url):
        parser = TinyGrabParser()
        try:
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            parser.feed(html)
        except:
            LOGGER.error(log.format(u'Unhandled exception in the tinygrab parser.'), exec_info=True)
            return None
        return {'url': parser.get_img(), 'format': 'standard'}

    def steam(url):
        parser = SteamParser()
        try:
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            parser.feed(html)
        except:
            LOGGER.error(log.format(u'Unhandled exception in the steam parser.'), exec_info=True)
            return None
        return {'url': parser.get_img(), 'format': 'standard'}

    def fivehpx(url):
        parser = FivehpxParser()
        try:
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            parser.feed(html)
        except:
            LOGGER.error(log.format(u'Unhandled exception in the 500px parser.'), exec_info=True)
            return None
        return {'url': parser.get_img(), 'format': 'standard'}

    def flickr(url):
        '''Flickr seems to do a lot of javascript voodoo after page load so tag searching is difficult'''
        try:
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            try:
                base_url = re.search("baseURL: '([^']+)'", html).groups()[0]
            except AttributeError:
                return None  # No match, no image.
            thumbnail = re.sub('(\d+_\w+)\.(\w+)$', '\g<1>_n.\g<2>', base_url)
        except:
            LOGGER.error(log.format(u'Unhandled exception in the flickr parser.'), exec_info=True)
            return None
        return {'url': thumbnail, 'format': 'standard'}

    def tinypic(url):
        # Need to add a unique identifier that doesn't break the url so unique
        # messages show up in the digest
        uniquifier = hashlib.md5()
        uniquifier.update(url)
        id = u'HauntingSociableGrayreefshark'
        hash = unicode(uniquifier.hexdigest())
        return {'url': url, 'html': _tinypic_gfycat_iframe.substitute(id=id, hash=hash), 'format': 'custom'}

    def deviantart(url):
        parser = DAParser()
        try:
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            parser.feed(html)
        except:
            LOGGER.error(log.format(u'Unhandled exception in the DA parser.'), exec_info=True)
            return None
        return {'url': parser.get_img(), 'format': 'standard'}

    def imgur(url):
        def process_url(bot, url):
            parser = ImgurParser()
            # No try except here, catching elsewhere
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            parser.feed(html)
            img = parser.get_img()
            return img

        # Imgur has a lot of shit urls, filter them first before trying to
        # parse the html.
        if re.search('user|\.com/?$|//[^\.\W]{2,}\.imgur.com', url, re.I):
            return None

        # Trim off trailing ?1 shit
        url = re.sub('(.*)\?\S*$', '\g<1>', url)
        if url.split('.')[-1] in FILELIST:
            # We just cleaned up a raw image link
            return {'url': url, 'format': 'standard'}

        # Turn mobile urls into normal
        url = re.sub('m\.imgur\.com', 'i.imgur.com', url)

        if re.search('gallery', url):
            try:
                # Turn gallery urls into albums
                processed_url = re.sub('gallery/([a-zA-Z0-9]{5,})(.*)', 'a/\g<1>', url)
                img = process_url(bot, processed_url)  # all this is really used for is to throw exceptions on 404s
                url = processed_url
            except:
                try:
                    # Turn gallery urls into image links
                    processed_url = re.sub('gallery/([a-zA-Z0-9]{5,})(.*)', '\g<1>', url)
                    img = process_url(bot, processed_url)
                except:
                    LOGGER.error(log.format(u'Unhandled exception in the imgur parser.'), exec_info=True)
                    return None
        else:
            try:
                img = process_url(bot, url)
            except:
                LOGGER.error(log.format(u'Unhandled exception in the imgur parser.'), exec_info=True)
                return None

        if img:
            # If we got an image back, process it a touch to get a smaller
            # image and then return it
            img = imgur_get_medium(bot, img)
            return {'url': img, 'format': 'standard'}
        else:
            # Else return the original url sans hash numbers for album embedding
            url = re.sub('(/[a-zA-Z0-9]{5,})/?#[0-9]*', '\g<1>', url)
            return {'url': url,
                    'html': _imgur_album.substitute(url=url),
                    'format': 'custom'}

    def dropbox(url):
        # TODO remove this if possible after header check is implemented
        try:
            if url.split('.')[-1] in FILELIST:
                formatted_url = re.sub(u'(www)?\.dropbox\.com', u'dl.dropboxusercontent.com', url, flags=re.I)
                return {'url': formatted_url, 'format': 'standard'}
            else:
                return None
        except:
            LOGGER.error(log.format(u'Unhandled exception in the dropbox parser.'), exec_info=True)
            return None

    def e621(url):
        id = re.search('post/show/(\d{5,})', url, flags=re.I)
        try:
            parsed = u'https://e621.net/post/show.json?id=%s' % id.groups()[0]
        except AttributeError:
            return None
        try:
            content = urllib2.urlopen(parsed)
            raw_json = content.read().decode('utf-8', 'replace')
            f_json = json.loads(raw_json)
            if 'file_url' in f_json:
                return {'url': f_json['file_url'], 'format': 'standard'}
            else:
                return None
        except:
            LOGGER.error(log.format(u'Unhandled exception in the e621 parser.'), exec_info=True)
            return None

    def gfycat(url):
        if url.endswith('/terms'):
            return None
        try:
            id = re.search('gfycat\.com/([a-zA-Z]{6,})', url).groups()[0]
        except AttributeError:
            return None
        # TODO make the custom format just take URL and HTML
        return {'url': url, 'html': _gfycat_iframe.substitute(id=id), 'format': 'custom'}

    LOGGER.info(log.format("Filtering URL %s"), url)

    parsed_url = urlparse.urlparse(url)
    domain = u'{uri.netloc}/'.format(uri=parsed_url).strip(u'/')
    # Regex replacements for certain domains
    LOGGER.info(log.format("Unprocessed domain is: %s"), domain)
    for r in _dom_map:
        domain = _dom_map[r].sub(r, domain)
    LOGGER.info(log.format("Processed domain is: %s"), domain)

    if url.split('.')[-1] in FILELIST:
        # TODO Grab header and see if MIME type is sane before returning the
        # raw link
        if domain not in temp_preprocess:
            LOGGER.info(log.format("Url %s appears a raw image link."), url)
            # For now, only imgur needs raw link modifications. If we do more
            # than just imgur, though, we'll need a lookup with functions.
            # Turn mobile urls into normal
            url = re.sub('m\.imgur\.com', 'i.imgur.com', url)

            orig = url
            if re.search('imgur\.com', url):
                url = imgur_get_medium(bot, url)
            html = _simple_img.substitute(url=url, orig=orig)  # format the html link or album
            return {'url': url, 'service': domain, 'html': html}

    # Try to get url function for specific domain
    try:
        check = domains[domain]
    except KeyError:
        LOGGER.warning(log.format("Domain %s not found."), domain)
        return None

    # If we got a check function, use that to return the image url
    if check:
        results = check(url)
    else:
        return None

    if results:
        if results['format'] == 'custom':
            html = results['html']
        else:  # Generic img, format == 'standard'
            html = _simple_img.substitute(url=results['url'], orig=url)  # format the html link or album
        try:
            return {'url': results['url'], 'service': domain, 'html': html}
        except TypeError:
            return None
    else:
        return None

url = re.compile(r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?]))''')
re_nsfw = re.compile(r'(?i)NSFW|suggestive|nude|questionable|explicit|porn|clop')


@rule(r'''(?i).*\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?]))''')
def url_watcher(bot, trigger):
    # Don't record stuff from private messages
    if not trigger.sender.startswith('#') or util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    # Don't record from commands
    if unicode(trigger).startswith('!') or unicode(trigger).startswith('.'):
        return
    # Ignore blacklisted urls
    for i in BLACKLIST:
        if re.search(i, unicode(trigger), re.I):
            return

    now = time.time()

    try:
        matches = [i[0] for i in url.findall(unicode(trigger))]
    except IndexError:
        LOGGER.error(log.format('Error finding all URLs in message - No urls found!'))
        LOGGER.error(('Message was: %s'), unicode(trigger))
        return

    time.sleep(20)  # Wait just a bit to grab post-link nsfw tagging context, but only once per message
    with bot.memory['digest']['context_lock']:
        local_context = [i for i in bot.memory['digest']['context']]

    for u in matches:
        original = u
        u = image_filter(bot, u)  # returns dictionary with url, service and html
        if not u:
            continue

        # NSFW checking. If the message line contains keywords, mark as NSFW. If
        # the context contains keywords, mark as unknown/maybe.
        # TODO catch SFW tags to override context
        nsfw = False
        if re_nsfw.search(unicode(trigger)):
            nsfw = True
        else:
            for i in [x[1] for x in local_context if x[0] == trigger.sender]:
                if re_nsfw.search(i):
                    nsfw = None
        if not u['url']:
            return
        t = {
            'time': now,
            'message': unicode(trigger),  # This is unicode
            'author': nicks.NickPlus(trigger.nick, trigger.host),
            'nsfw': nsfw,
            'url': original,  # This is unicode
            'image': u['url'],  # This is unicode
            'service': u['service'].decode('utf-8', 'replace'),
            'html': u['html'],  # this is unicode?
            'channel': trigger.sender,
            'reported': False
            }
        with bot.memory['digest']['lock']:
            bot.memory['digest']['digest'].append(t)
            write_to_db(bot, t)
        LOGGER.info(log.format("raw object", pp(t)))


@commands('digest_clear')
def digest_clear(bot, trigger):
    '''Clears all links from the image digest. Admin only.'''
    if not trigger.owner:
        return
    with bot.memory['digest']['lock']:
        bot.memory['digest']['digest'] = []
        db_refresh(bot)
    bot.reply(u'Cleared.')


@commands('digest_refresh_db')
def digest_db_refresh(bot, trigger):
    '''Force overwrites the db with what's in memory. Admin only.'''
    if not trigger.owner:
        return
    LOGGER.info(log.format('Starting db refresh.'))
    with bot.memory['digest']['lock']:
        db_refresh(bot)
    LOGGER.info(log.format('DB refresh complete.'))
    bot.reply('Database refresh complete.')


def db_refresh(bot):
    '''Clears and rewrites database entries. Assumes this is being called inside a lock'''
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    try:
        cur.execute('delete from digest')
        dbcon.commit()
    except:
        LOGGER.error(log.format(u'Unhandled database exception when clearing table.'), exec_info=True)
    finally:
        cur.close()
    # Write every image item to the database
    for item in bot.memory['digest']['digest']:
        write_to_db(bot, item)


def write_to_db(bot, item):
    '''Writes a single item passed as a dict to the database. Assumes this is being called inside a lock'''
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    try:
        cur.execute('''
                    insert into digest (time, message, author, nsfw, url, image, service, channel, reported, html)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (item['time'],
                          item['message'],  # Should be unicode at this point
                          item['author'],
                          parsebool(item['nsfw']),
                          item['url'],  # Should be unicode at this point
                          item['image'],  # Should be unicode at this poit
                          item['service'],
                          item['channel'],
                          parsebool(item['reported']),
                          item['html']))
        dbcon.commit()
    except:
        LOGGER.error(log.format(u'Unhandled database exception when inserting image.'), exec_info=True)
        LOGGER.error('raw item', pp(item), exec_info=True)
    finally:
        cur.close()


@commands('digest_dump')
def digest_dump(bot, trigger):
    '''Dumps digest debugging data to log. Admin only.'''
    if not trigger.owner:
        return
    with bot.memory['digest']['lock']:
        bot.reply(u'Dumping digest to logs.')
        LOGGER.debug(log.format('=' * 20))
        LOGGER.debug(log.format('time is %s' % time.time()))
        for i in bot.memory['digest']['digest']:
            LOGGER.debug(log.format(pp(i)))
        LOGGER.debug(log.format('=' * 20))


@interval(60)
def clean_links(bot):
    '''Remove old links from bot memory'''
    with bot.memory['digest']['lock']:
        bot.memory['digest']['digest'] = [i for i in bot.memory['digest']['digest'] if i['time'] > time.time() - EXPIRATION]
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            t = time.time() - EXPIRATION
            cur.execute('delete from digest where time < ?', (t,))
            dbcon.commit()
        except:
            LOGGER.error(log.format(u'Unhandled database exception when cleaning up old links.'), exec_info=True)
        finally:
            cur.close()


@rule('.*')
def context(bot, trigger):
    '''Function to keep a running context of messages.'''
    with bot.memory['digest']['context_lock']:
        bot.memory['digest']['context'].append((trigger.sender, unicode(trigger)))

        # Trim list to keep it contextual
        if len(bot.memory['digest']['context']) > 20:
            bot.memory['digest']['context'].pop(0)


@commands('context_clear')
def context_clear(bot, trigger):
    '''Clears the running chat context used for NSFW tagging. Admin only.'''
    if not trigger.owner:
        return
    with bot.memory['digest']['context_lock']:
        bot.memory['digest']['context'] = []
    bot.reply(u'Cleared.')


@commands('digest_url_dump')
def url_dump(bot, trigger):
    '''Dumps digest urls to the log. Admin only.'''
    if not trigger.owner:
        return
    with bot.memory['digest']['lock']:
        bot.reply(u'Dumping digest urls to logs.')
        LOGGER.debug(log.format('=' * 20))
        for i in bot.memory['digest']['digest']:
            LOGGER.debug(log.format(i['image']))
        LOGGER.debug(log.format('=' * 20))


@commands('digest_build_html')
def build_html(bot, trigger):
    '''Force builds the HTML page for the image digest. Admin only.'''
    def is_nsfw(nsfw, reported):
        if nsfw or reported:
            return "<b>This image was tagged as NSFW - Click to reveal.</b>"
        elif nsfw is None:
            return "<b>This image may be NSFW - Click to reveal.</b> (flagged from conversation context)"
        else:
            return "SFW"

    def build_links(link_list):
        ''' Returns a dictionary like so
        {'http://example.com/image.png':
            {'url': 'http://example.com/images/1899691',
             'nsfw': False,
             'service': 'fav.me',
             'reported': False,
             'messages':
                 [{'author': 'eytosh',
                   'time': '187273918392.187',
                   'message': 'Here\'s something neat: http://example.com/images/1899691'},
                  {'author': 'beerpony',
                   'time': '162734282347.234',
                   'message': "wtf http://example.com/images/1899691"}]
            },
         '\\example2.png': {...}
        }
        '''

        with bot.memory['digest']['lock']:
            parsed_links = {}
            for link in link_list:
                if link['image'].lower() in parsed_links:
                    parsed_links[link['image'].lower()]['messages'].append({
                        'author': link['author'],
                        'time': link['time'],
                        'message': link['message'],
                        'channel': link['channel']})
                    # Sort to ensure element 0 is oldest message
                    parsed_links[link['image'].lower()]['messages'].sort(key=lambda t: t['time'])
                else:
                    parsed_links[link['image'].lower()] = {
                        'image': link['image'],
                        'html': link['html'],
                        'nsfw': link['nsfw'],
                        'url': link['url'],
                        'service': link['service'],
                        'reported': link['reported'],
                        'messages': [{
                            'author': link['author'],
                            'time': link['time'],
                            'message': link['message'],
                            'channel': link['channel']}]}
            return parsed_links

    if trigger:
        if not trigger.owner:
            return
        LOGGER.info(log.format(u'Building HTML on command'))

    try:
        with open(bot.memory['digest']['destination'], 'r') as f:
            previous_html = ''.join(f.readlines())
    except IOError:
        previous_html = u''
        LOGGER.warning(log.format(u'IO error grabbing "list_main_dest_path" file contents. File may not exist yet'), exec_info=True)

    # Generate HTML
    # TODO Add check to see if the image is still available and remove those
    # that aren't
    header = Template('${title}${script}${style}')
    header_title = '<title>Image digest</title>'

    simple_header = header.substitute(
        title=header_title,
        script=_header_script,
        style=_style)

    # TODO move these
    # First deduplicate our links
    dedupe = build_links(bot.memory['digest']['digest'])
    if dedupe:
        # Next make into a list for sorting
        # TODO move this into the dedupe function ?
        dedupe_list = [{'image': dedupe[i]['image'],
                        'html': dedupe[i]['html'],
                        'url': dedupe[i]['url'],
                        'nsfw': is_nsfw(dedupe[i]['nsfw'], dedupe[i]['reported']),
                        'author': dedupe[i]['messages'][0]['author'],
                        'channel': dedupe[i]['messages'][0]['channel'],
                        'message': dedupe[i]['messages'][0]['message'],
                        'time': dedupe[i]['messages'][0]['time']
                        } for i in dedupe]
        dedupe_list.sort(key=lambda t: t['time'], reverse=True)  # Sort the list by post time

        msg = u'\n'.join(
            [_img_div_nsfw.substitute(
                img=i['html'],
                desc=_desc_div.substitute(
                    author=i['author'],
                    channel=i['channel'],
                    message=i['message'],
                    ftime=datetime.utcfromtimestamp(i['time']).strftime('%H:%M UTC - %b %d, %Y'),
                    nsfw=i['nsfw'])
            ) if re.search('NSFW', i['nsfw']) else
                _img_div.substitute(
                img=i['html'],
                desc=_desc_div.substitute(
                    author=i['author'],
                    channel=i['channel'],
                    message=i['message'],
                    ftime=datetime.utcfromtimestamp(i['time']).strftime('%H:%M UTC - %b %d, %Y'),
                    nsfw=i['nsfw'])
            )
                for i in dedupe_list]
        )
    else:
        msg = u''

    html = bot.memory['digest']['templatehtml'].substitute(body=msg, head=simple_header)
    if previous_html.decode('utf-8', 'replace') != html:
        LOGGER.info(log.format(u'Generated digest html file is different, writing.'))
        with open(bot.memory['digest']['destination'], 'w') as f:
            f.write(html.encode('utf-8', 'replace'))


@interval(60)
def build_regularly(bot):
    build_html(bot, None)


@commands('report')
@example('!report http://imgur.com/notarealurl')
def report(bot, trigger):
    '''Report an url on the image digest page as NSFW.'''
    try:
        target = trigger.args[1].split()[1]
    except IndexError:
        bot.reply('You gave me nothing to report!')
        return
    if not re.search('^https?://', target):
        target = u'http://%s' % target
    with bot.memory['digest']['lock']:
        bad_stuff_happened = False
        for i in bot.memory['digest']['digest']:
            if target == i['image'] or target == i['url']:
                i['reported'] = True
                dbcon = bot.db.connect()
                cur = dbcon.cursor()
                try:
                    cur.execute('''update digest set reported = ? where url = ? or image = ?''',
                                (parsebool(True), target, target))
                    dbcon.commit()
                except:
                    LOGGER.error(log.format(u'Unhandled database exception when reporting link.'), exec_info=True)
                    bad_stuff_happened = True
                finally:
                    cur.close()
        if bad_stuff_happened:
            bot.reply("Sorry, something went wrong. This bug has been recorded.")
        else:
            bot.reply("Thank you for reporting that link. The update will be reflected on the page shortly.")


@commands('unreport')
@example('!unreport http://imgur.com/notarealurl')
def unreport(bot, trigger):
    '''Unmark an url on the image digest page as NSFW.
    This will not mark an explicitly tagged image as safe,
    only reported images. Admin only.'''
    if not trigger.admin:
        return
    pass
    try:
        target = trigger.args[1].split()[1]
    except IndexError:
        bot.reply('You gave me nothing to report!')
        return
        target = u'http://%s' % target
    with bot.memory['digest']['lock']:
        for i in bot.memory['digest']['digest']:
            if target == i['image'] or target == i['url']:
                i['reported'] = False
                bad_stuff_happened = False
                dbcon = bot.db.connect()
                cur = dbcon.cursor()
                try:
                    cur.execute('''update digest set reported = ? where url = ? or image = ?''',
                                (parsebool(False), target, target))
                    dbcon.commit()
                except:
                    LOGGER.error(log.format(u'Unhandled database exception when reporting link.'), exec_info=True)
                    bad_stuff_happened = True
                finally:
                    cur.close()
        if bad_stuff_happened:
            bot.reply("Something broke!")
        else:
            bot.reply("Done")


@commands('remove', 'digest_remove')
@example('!remove http://imgur.com/notarealurl')
def remove(bot, trigger):
    '''Vote to remove a link from the image digest.'''
    def do_remove(bot, link):
        with bot.memory['digest']['lock']:
            for i in bot.memory['digest']['digest']:
                if link == i['image'] or link == i['url']:
                    bot.memory['digest']['digest'].remove(i)
            dbcon = bot.db.connect()
            cur = dbcon.cursor()
            try:
                cur.execute('delete from digest where url = ? or image = ?', (link, link))
                dbcon.commit()
            except:
                LOGGER.error(log.format(u'Unhandled database exception when reporting link.'), exec_info=True)
                return False
            else:
                return True
            finally:
                cur.close()

    # Don't allow private messages
    if not trigger.sender.startswith('#'):
        return

    try:
        target = trigger.args[1].split()[1]
    except IndexError:
        bot.reply('You gave me nothing to remove!')
        return

    if not trigger.admin:
        if bot.memory['digest']['to_remove']:
            with bot.memory['digest']['lock']:
                # Vote is active. Record vote, remove, or say if wrong thing to vote on.
                if target == bot.memory['digest']['to_remove']:
                    # A vote for the current link
                    if bot.memory['digest']['count'] == _REMOVE_VOTES - 1:
                        # We have enough votes now, remove it
                        if do_remove(bot, target):
                            bot.say('Link removed. The page will update shortly.')
                            bot.memory['digest']['to_remove'] = None
                            bot.memory['digest']['count'] = 0
                        else:
                            bot.reply("Sorry, something went wrong. This bug has been recorded.")
                    else:
                        # Not enough votes yet, add one
                        bot.memory['digest']['count'] += 1
                        bot.reply('%i votes of %i needed to remove.' % (bot.memory['digest']['count'], _REMOVE_VOTES))
                else:
                    bot.reply("Sorry, currently voting on %s" % bot.memory['digest']['to_remove'])
        else:
            # Not voting on anything yet, set up new vote.
            with bot.memory['digest']['lock']:
                exists = False
                for i in bot.memory['digest']['digest']:
                    if target == i['image'] or target == i['url']:
                        exists = True
                        break
                if exists:
                    bot.memory['digest']['to_remove'] = target
                    bot.memory['digest']['count'] = 1
                    bot.say('Link removal vote started for %s. %i more votes in the next %i minutes are required.' %
                            (target, _REMOVE_VOTES - 1, _VOTE_TIME))
                else:
                    bot.reply("I couldn't find that link on the digest page to remove.")
            time.sleep(_VOTE_TIME * 60)
            with bot.memory['digest']['lock']:
                bot.memory['digest']['to_remove'] = None
                bot.memory['digest']['count'] = 0

    else:
        if do_remove(bot, target):
            bot.reply('Done')
        else:
            bot.reply('Something broke!')
        bot.memory['digest']['to_remove'] = None
        bot.memory['digest']['count'] = 0


if __name__ == "__main__":
    print(__doc__.strip())
