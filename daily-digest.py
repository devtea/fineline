"""
daily-digest.py - A Willie module that summarizes and displays images posted in the last day
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import json
import re
import threading
import time
import traceback
import types
import urlparse
import urllib2
from datetime import datetime
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
IGNORE = ['hushmachine', 'hushbot', 'hushrobot', 'fineline', 'feignline']


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
    if 'context' not in bot.memory['digest']:
        bot.memory['digest']['context'] = []
    if 'lock' not in bot.memory['digest']:
        bot.memory['digest']['lock'] = threading.Lock()
    if 'context_lock' not in bot.memory['digest']:
        bot.memory['digest']['context_lock'] = threading.Lock()

    # Load config values
    bot.memory['digest']['template'] = bot.config.dailydigest.template
    bot.memory['digest']['destination'] = bot.config.dailydigest.destination
    bot.memory['digest']['url'] = bot.config.dailydigest.url
    with open(bot.memory['digest']['template'], 'r') as f:
        try:
            bot.memory['digest']['templatehtml'] = Template(f.read().decode('utf-8', 'replace'))
        except:
            bot.debug(__file__, log.format(u'Unable to load template.'), u'always')
            raise

    with bot.memory['digest']['lock']:
        bot.memory['digest']['some_dictionary'] = {}

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
                            reported integer)''')
            db.commit()
            cur.execute('SELECT time, message, author, nsfw, url, image, service, channel, reported FROM digest')
            query = cur.fetchall()
        finally:
            cur.close()
            db.close()
        if query:
            bot.memory['digest']['digest'] = []
            for t, m, a, n, u, i, s, c, r in query:
                item = {
                    'time': t,
                    'message': m.decode('utf-8', 'replace'),
                    'author': nicks.NickPlus(a.decode('utf-8', 'replace')),
                    'nsfw': parsebool(n),
                    'url': u.decode('utf-8', 'replace'),
                    'image': i.decode('utf-8', 'replace'),
                    'service': s.decode('utf-8', 'replace'),
                    'channel': c.decode('utf-8', 'replace'),
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


@commands(u'dd', u'dailydigest', u'digest')
def template(bot, trigger):
    """Displays the configured url for the daily digest page."""
    bot.say(u'The daily image digest page is at %s' % bot.memory['digest']['url'])


def image_filter(bot, url):
    '''Filter URLs for known image hosting services and raw image links'''
    # TODO Image services to Support
    # Imgur (mostly just gallery embedding now)
    # Grab.by ?
    # Steam
    # misc boorus
    # 500px
    # flickr
    FILELIST = ['png', 'jpg', 'jpeg', 'tiff', 'gif', 'bmp', 'svg']
    _dom_map = {
        'deviantart.net': re.compile('\S+\.deviantart\.net'),
        'deviantart.com': re.compile('\S+\.deviantart\.com'),
        'imgur.com': re.compile('i\.imgur\.com')
    }
    domains = {
        'deviantart.net': (lambda url: deviantart(url)),
        'deviantart.com': (lambda url: deviantart(url)),
        'sta.sh': (lambda url: deviantart(url)),
        'fav.me': (lambda url: deviantart(url)),
        'dropbox.com': (lambda url: dropbox(url)),
        'www.dropbox.com': (lambda url: dropbox(url)),
        'i.imgur.com': (lambda url: imgur(url)),
        'imgur.com': (lambda url: imgur(url)),
        'derpiboo.ru': (lambda url: derpibooru(url)),
        'derpibooru.org': (lambda url: derpibooru(url)),
        'trixiebooru.org': (lambda url: derpibooru(url)),
        'derpicdn.net': (lambda url: derpibooru(url)),
        'cdn.derpiboo.ru': (lambda url: derpibooru(url)),
        'static1.e621.net': (lambda url: e621(url)),
        'e621.net': (lambda url: e621(url))
    }
    temp_preprocess = ['dropbox.com', 'www.dropbox.com']  # Temporary list to specify which need to be preprocessed

    def derpibooru(url):
        '''derpibooru provides an oembed option at derpiboo.ru/oembed.json'''
        try:
            content = urllib2.urlopen(u"http://derpiboo.ru/oembed.json?url=%s" % url)
            raw_json = content.read().decode('utf-8', 'replace')
            f_json = json.loads(raw_json)
            if 'thumbnail_url' in f_json:
                return f_json['thumbnail_url']
            else:
                return None
        except:
            bot.debug(__file__, log.format(u'Unhandled exception in the derpibooru parser.'), 'warning')
            bot.debug(__file__, traceback.format_exc(), 'warning')
            return None

    def deviantart(url):
        parser = DAParser()
        try:
            content = urllib2.urlopen(url)
            html = content.read().decode('utf-8', 'replace')
            parser.feed(html)
        except:
            bot.debug(__file__, log.format(u'Unhandled exception in the DA parser.'), 'warning')
            bot.debug(__file__, traceback.format_exc(), 'warning')
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
            bot.debug(__file__, log.format(u'Unhandled exception in the imgur parser.'), 'warning')
            bot.debug(__file__, traceback.format_exc(), 'warning')
            return None
        img = parser.get_img()
        if img:
            # If we got an image back, return it
            return img
        else:
            # Else return the original URL for album embedding
            return url

    def dropbox(url):
        # TODO remove this if possible after header check is implemented
        try:
            if url.split('.')[-1] in FILELIST:
                return re.sub('(www)?\.dropbox\.com', 'dl.dropboxusercontent.com', url, flags=re.I)
            else:
                return None
        except:
            bot.debug(__file__, log.format(u'Unhandled exception in the dropbox parser.'), 'warning')
            bot.debug(__file__, traceback.format_exc(), 'warning')
            return None

    def e621(url):
        id = re.search('post/show/(\d{5,})', url, flags=re.I)
        if not id:
            return None
        parsed = u'https://e621.net/post/show.json?id=%s' % id.groups()[0]
        try:
            content = urllib2.urlopen(parsed)
            raw_json = content.read().decode('utf-8', 'replace')
            f_json = json.loads(raw_json)
            if 'file_url' in f_json:
                return f_json['file_url']
            else:
                return None
        except:
            bot.debug(__file__, log.format(u'Unhandled exception in the e621 parser.'), 'warning')
            bot.debug(__file__, traceback.format_exc(), 'warning')
            return None

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
        # TODO Grab header and see if MIME type is sane before returning the
        # raw link
        if domain not in temp_preprocess:
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
        # TODO catch SFW tags to override context
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
            write_to_db(bot, t)
        bot.debug(__file__, log.format(pp(t)), 'verbose')


@commands('digest_refresh_db')
def digest_db_refresh(bot, trigger):
    if not trigger.owner:
        return
    with bot.memory['digest']['lock']:
        db_refresh(bot)
    bot.reply('Database refresh complete.')


def db_refresh(bot):
    '''Clears and rewrites database entries. Assumes this is being called inside a lock'''
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    try:
        cur.execute('delete from digest')
        dbcon.commit()
    except:
        bot.debug(__file__, log.format(u'Unhandled database exception when clearing table.'), 'warning')
        bot.debug(__file__, traceback.format_exc(), 'warning')
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
                    insert into digest (time, message, author, nsfw, url, image, service, channel, reported)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (item['time'], item['message'], item['author'], parsebool(item['nsfw']),
                            item['url'], item['image'], item['service'], item['channel'],
                            parsebool(item['reported'])))
        dbcon.commit()
    except:
        bot.debug(__file__, log.format(u'Unhandled database exception when inserting image.'), 'warning')
        bot.debug(__file__, pp(item), 'warning')
        bot.debug(__file__, traceback.format_exc(), 'warning')
    finally:
        cur.close()


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
        # Clearing the whole DB every time is inefficient, but simple. Thankfully
        # this should never be a very large operation.
        db_refresh(bot)



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
_style = '''
    <style>
    div.img {
        margin: 5px;
        padding: 5px;
        border: 1px solid #000000;
        height: auto;
        width: auto;
        float: left;
        text-align: center;
    }
    div.img img {
        display: inline;
        margin: 5px;
        border: 1px solid #ffffff;
    }
    div.img a:hover img {
        border:1px solid #0000ff;
    }
    div.desc {
        text-align: left ;
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


@commands('digest_build_html')
def build_html(bot, trigger):
    def is_nsfw(nsfw):
        if nsfw is None:
            return "<b>This image may be NSFW</b> (flagged from conversation context)"
        elif nsfw:
            return "<b>This images was tagged as NSFW</b>"
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

    try:
        with open(bot.memory['digest']['destination'], 'r') as f:
            previous_html = ''.join(f.readlines())
    except IOError:
        previous_html = ''
        bot.debug(__file__, log.format(u'IO error grabbing "list_main_dest_path" file contents. File may not exist yet'), 'warning')

    # Generate HTML
    # TODO Add check to see if the image is still available and remove those
    # that aren't
    header = Template('${title}${style}')
    header_title = '<title>Image digest - Warning, NSFW is not hidden yet!</title>'
    simple_header = header.substitute(title=header_title, style=_style)

    img_div = Template('<div class = "img">${img}${desc}</div>')
    simple_img = Template('<a href="${orig}"><img src="${url}" height="250"></a>')
    desc_div = Template(_desc)
    # First deduplicate our links
    dedupe = build_links(bot.memory['digest']['digest'])
    if dedupe:
        # Next make into a list for sorting
        # TODO move this into the dedupe function
        dedupe_list = [{'image': dedupe[i]['image'],
                        'url': dedupe[i]['url'],
                        'nsfw': is_nsfw(dedupe[i]['nsfw']),
                        'author': dedupe[i]['messages'][0]['author'],
                        'channel': dedupe[i]['messages'][0]['channel'],
                        'message': dedupe[i]['messages'][0]['message'],
                        'time': dedupe[i]['messages'][0]['time']
                        } for i in dedupe]
        dedupe_list.sort(key=lambda t: t['time'], reverse=True)

        msg = '\n'.join(
            [img_div.substitute(
                img=simple_img.substitute(
                    url=i['image'],
                    orig=i['url']),
                desc=desc_div.substitute(
                    author=i['author'],
                    channel=i['channel'],
                    message=i['message'],
                    ftime=datetime.utcfromtimestamp(i['time']).strftime('%H:%M UTC - %b %d, %Y'),
                    nsfw=i['nsfw']
                )
            ) for i in dedupe_list]
        )
    else:
        msg = ''

    html = bot.memory['digest']['templatehtml'].substitute(
        body=msg,
        head=simple_header
    )
    if previous_html != html:
        bot.debug(__file__, log.format(u'Generated digest html file is different, writing.'), u'verbose')
        with open(bot.memory['digest']['destination'], 'w') as f:
            f.write(html.encode('utf-8'))


@interval(60)
def build_regularly(bot):
    build_html(bot, None)


if __name__ == "__main__":
    print(__doc__.strip())
