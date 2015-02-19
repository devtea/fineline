"""
streams.py - A willie module to track livestreams from popular services
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import json
import re
import shutil
from socket import timeout
from string import Template
import threading
import time

from willie.logger import get_logger
from willie.module import commands, interval
from willie.tools import Identifier
import willie.web as web

LOGGER = get_logger(__name__)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    import os.path
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()

try:
    import colors
except:
    import imp
    import sys
    import os.path
    try:
        LOGGER.info(log.format("Trying manual import of colors formatter."))
        fp, pathname, description = imp.find_module('colors', [os.path.join('.', '.willie', 'modules')])
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
    finally:
        if fp:
            fp.close()

_exc_regex = []
_twitch_client_id = None  # Overwritten in setup()
_youtube_api_key = None  # Overwritten in setup()
_ustream_dev_key = None  # Overwritten in setup()
_re_ttv = re.compile('(?<=twitch\.tv/)[^/(){}[\]]+')
_exc_regex.append(re.compile('twitch\.tv/'))
_re_ls = re.compile('(?<=livestream\.com/)[^/(){}[\]]+')
_exc_regex.append(re.compile('livestream\.com/'))
_re_us = re.compile('((?<=ustream\.tv/channel/)|(?<=ustream\.tv/))([^/(){}[\]]+)')
_exc_regex.append(re.compile('ustream\.tv/'))
_re_yt = re.compile('((youtube\.com/user/)|(youtube\.com/))([^\?/(){}[\]\s]+)')
_exc_regex.append(re.compile('youtube\.com/'))
_re_pic = re.compile('(?<=picarto\.tv/live/channel.php\?watch=)[^/(){}[\]]+')
_exc_regex.append(re.compile('picarto\.tv/'))
# _url_finder = re.compile(r'(?u)(%s?(?:http|https)(?:://\S+))')
_services = ['twitch.tv', 'livestream.com', 'youtube.com', 'ustream.tv', 'picarto.tv']
# TODO move this to memory
_include = ['#reddit-mlpds', '#fineline_testing']


class stream(object):
    '''General stream object. To be extended for each individual API.'''
    _alias = None
    _url = None
    _settings = {}
    _live = False
    _nsfw = False
    _manual_nsfw = False
    _last_update = None
    _service = None

    def __init__(self, name, alias=None):
        super(stream, self).__init__()
        self._name = name
        self._alias = alias

    def __str__(self):
        # TODO parse unicode to str
        return '%s on %s' % (self.name, self.service)

    def __unicode__(self):
        return '%s on %s' % (self.name, self.service)

    def __repr__(self):
        return self._name

    def __lt__(self, other):
        return ((self.name, self.service) < (other.name, other.service))

    def __le__(self, other):
        return ((self.name, self.service) <= (other.name, other.service))

    def __gt__(self, other):
        return ((self.name, self.service) > (other.name, other.service))

    def __ge__(self, other):
        return ((self.name, self.service) >= (other.name, other.service))

    def __eq__(self, other):
        return ((self.name, self.service) == (other.name, other.service))

    def __ne__(self, other):
        return ((self.name, self.service) != (other.name, other.service))

    def __hash__(self):
        return hash((self.name, self.service))

    @property
    def live(self):
        return self._live

    @live.setter
    def live(self, value):
        assert isinstance(value, bool)
        self._live = value

    @property
    def name(self):
        return self._name

    @property
    def service(self):
        return self._service

    @property
    def url(self):
        return self._url

    @property
    def nsfw(self):
        return self._nsfw

    @property
    def m_nsfw(self):
        return self._manual_nsfw

    @m_nsfw.setter
    def m_nsfw(self, value):
        assert isinstance(value, bool)
        self._manual_nsfw = value

    @m_nsfw.deleter
    def m_nsfw(self):
        self._manual_nsfw = None

    @property
    def alias(self):
        return self._alias

    @alias.setter
    def alias(self, value):
        assert isinstance(value, str)
        self._alias = value

    @alias.deleter
    def alias(self):
        self._alias = None

    @property
    def updated(self):
        return self._last_update

    def update(self):
        # Dummy function to be extended by children. Use to hit the appropriate
        # streaming site and update object variables.
        return


class livestream(stream):
    # http://www.livestream.com/userguide/index.php?title=Channel_API_2.0
    _base_url = '.api.channel.livestream.com/2.0/'
    _service = 'livestream.com'
    _last_update = time.time()
    # _header_info = ''

    def __init__(self, name, alias=None):
        super(livestream, self).__init__(name, alias)
        self._safename = re.sub('_', '-', self._name)
        try:
            self._results = web.get('x%sx%sinfo.json' % (
                self._safename, self._base_url))
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            LOGGER.info(time.strftime("%Y-%m-%d %H:%M:%S"))
            if re.findall('400 Bad Request', self._results):
                LOGGER.warning(log.format('Livestream Error: 400 Bad Request'))
                raise ValueError('400 Bad Request')
            elif re.findall('404 Not Found', self._results):
                LOGGER.warning(log.format('Livestream Error: 404 Not Found'))
                raise ValueError('404 Not Found')
            elif re.findall('500 Internal Server Error', self._results):
                LOGGER.warning(log.format('Livestream Error: 500 Internal Server Error'))
                raise ValueError('500 Internal Server Error')
            elif re.findall('503 Service Unavailable', self._results):
                LOGGER.warning(log.format('Livestream Error: 503 Service Unavailable'))
                raise ValueError('503 Service Unavailable')
            else:
                LOGGER.warning(log.format("Bad Json loaded from livestream.com"), exc_info=True)
                LOGGER.warning("Raw data:")
                LOGGER.warning(self._results)
                raise
        for s in self._form_j['channel']:
            self._settings[s] = self._form_j['channel'][s]
        if not self._live and self._settings['isLive']:
            self._live = self._settings['isLive']
            self._last_update = time.time()
        self._url = self._settings['link']
        # No integrated NSFW flags to parse!

    def update(self):
        try:
            self._results = web.get('x%sx%slivestatus.json' % (
                self._safename, self._base_url))
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            if re.findall('400 Bad Request', self._results):
                LOGGER.warning(log.format('Livestream Error: 400 Bad Request'))
                raise ValueError('400 Bad Request')
            elif re.findall('404 Not Found', self._results):
                LOGGER.warning(log.format('Livestream Error: 404 Not Found'))
                raise ValueError('404 Not Found')
            elif re.findall('500 Internal Server Error', self._results):
                LOGGER.warning(log.format('Livestream Error: 500 Internal Server Error'))
                raise ValueError('500 Internal Server Error')
            elif re.findall('503 Service Unavailable', self._results):
                LOGGER.warning(log.format('Livestream Error: 503 Service Unavailable'))
                raise ValueError('503 Service Unavailable')
            else:
                LOGGER.warning(log.format("Bad Json loaded from livestream.com"), exc_info=True)
                LOGGER.warning("Raw data:")
                LOGGER.warning(self._results)
                raise
        for s in self._form_j['channel']:
            self._settings[s] = self._form_j['channel'][s]
        if bool(self._live) ^ bool(self._settings['isLive']):
            self._live = self._settings['isLive']
            self._last_update = time.time()


class ustream(stream):
    # bot.memory['streamSet']['ustream_dev_key'] = bot.config.streams.ustream_dev_key
    # http://developer.ustream.tv/data_api/docs
    _base_url = 'http://api.ustream.tv/json'
    _service = 'ustream.tv'
    _last_update = time.time()
    # _header_info = ''

    def __init__(self, name, alias=None):
        super(ustream, self).__init__(name, alias)
        self._results = web.get('%s/channel/%s/getInfo?key=%s' % (
            self._base_url, self._name, _ustream_dev_key))
        self._form_j = json.loads(self._results)
        if self._form_j['error']:
            raise ValueError(self._form_j['error'])
        if self._form_j['results']['status'] == 'online':
            self._live = True
            self._last_update = time.time()
        self._url = self._form_j['results']['url']
        # No integrated NSFW flags to parse

    def update(self):
        self._results = web.get('%s/channel/%s/getValueOf/status?key=%s' % (
            self._base_url, self._name, _ustream_dev_key))
        self._form_j = json.loads(self._results)
        if self._form_j['error']:
            raise ValueError(self._form_j['error'])
        if self._live ^ bool(self._form_j['results'] == 'live'):
            self._live = bool(self._form_j['results'] == 'live')
            self._last_update = time.time()


class picarto(stream):
    _user_url = 'https://www.picarto.tv/live/channel.php?watch=%s'
    _live_url = 'https://www.picarto.tv/live/api.php?channel=%s'
    _service = 'picarto.tv'

    _last_update = time.time()

    def __init__(self, name, alias=None):
        super(picarto, self).__init__(name, alias)
        self._name = self.verify_user(self._name)
        self._url = self._user_url % self._name
        self.update()

    def verify_user(self, channel):
        '''Try to hit user's page. Site will correct miscapitalizations.'''
        self._results = web.get(self._user_url % self._name)
        # Valid users will have a number of "watch=username" pairs. Invalid
        # users will have empty "watch=" attributes.
        self._corrected = re.findall(r'watch=([^"\']*)', self._results, flags=re.I)[0]
        if self._corrected:
            return self._corrected
        raise ValueError("Invalid username")

    def update(self):
        self._results = web.get(self._live_url % self._name)
        try:
            self.json_data = json.loads(self._results)
            if self.json_data['streamer-data']['online'] == '1':
                self._live = True
            else:
                self._live = False
        except:
            LOGGER.warning(log.format("Bad Json loaded from picarto.tv"), exc_info=True)
            LOGGER.warning("Raw data:")
            LOGGER.warning(self._results)
            self._live = False
            raise


class youtube(stream):
    _base_url = 'https://gdata.youtube.com/feeds/api/'
    _user_url = 'users/%s?alt=json'
    _live_url = 'users/%s/live/events?alt=json&status=active'
    _event_url = None
    _service = 'youtube.com'
    _header = {'GData-Version': 2}
    _re_yturl = re.compile('[^/]+$')

    if _youtube_api_key:
        _header['X-GData-Key'] = 'key=%s' % _youtube_api_key
    _last_update = time.time()

    def __init__(self, name, alias=None):
        super(youtube, self).__init__(name, alias)
        self._results = web.get(self._base_url + self._user_url % self._name,
                                headers=self._header)
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            # TODO May not need to handle this here, but in calling code
            raise
        # self._name = self._form_j['entry']['author'][0]['name']['$t']
        self._url_list = self._form_j['entry']['link']
        # for d in [a for a in self._url_list if a['rel'] == 'alternate']:
        #    # TODO make sure this url is the live url, probably not
        #    self._url = d['href']
        self._url = 'http://youtube.com/%s' % self._form_j['entry']['yt$username']['$t']
        self.update()

    @property
    def url(self):
        if self._event_url:
            return self._event_url
        else:
            return self._url

    def update(self):
        self._results = web.get(self._base_url + self._live_url % self._name,
                                headers=self._header)
        self._form_j = json.loads(self._results)
        if bool('entry' in self._form_j['feed']) ^ bool(self._live):
            if 'entry' in self._form_j['feed']:
                self._live = True
            else:
                self._live = False
            self._last_update = time.time()
            if self._live:
                # When going online, we should grab the live stream URL
                LOGGER.info(log.format('youtube live stream url %s'), self._form_j['feed']['entry'][0]['content']['src'])
                self._event_url = 'http://youtube.com/watch?v=%s' % \
                    self._re_yturl.findall(self._form_j['feed']['entry'][0]['content']['src'])[0]
            else:
                # when going offline, we should reset the URL
                self._event_url = None


class twitchtv(stream):
    _base_url = 'https://api.twitch.tv/kraken/'
    _service = 'twitch.tv'
    _header_info = {'Accept': 'application/vnd.twitchtv.v2+json'}
    if _twitch_client_id:
        _header_info['Client-ID'] = _twitch_client_id
    _last_update = time.time()

    def __init__(self, name, alias=None):
        super(twitchtv, self).__init__(name, alias)
        # Update channel info
        try:
            self._results = web.get('%schannels/%s' % (
                self._base_url, self._name), headers=self._header_info)
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            LOGGER.error(log.format("Bad Json loaded from twitch.tv"), exc_info=True)
            LOGGER.error("Raw data is:")
            LOGGER.error(self._results)
            raise
        if 'error' in self._form_j:
            raise ValueError('%s %s: %s' % (
                self._form_j['status'],
                self._form_j['error'],
                self._form_j['message']))
        # LOGGER.info(log.format('got json'))
        # LOGGER.info(json.dumps(self._form_j, indent=4))
        try:
            raise ValueError(self._form_j['error'])
        except KeyError:
            pass
        for s in self._form_j:
            self._settings[s] = self._form_j[s]
        self._form_j = None  # cleanup
        self._url = self._settings['url']
        # NSFW flag is one of ['true', 'false', None]
        if self._settings['mature'] == 'true':
            self._nsfw = True
        else:
            self._nsfw = False
        self.update()

    def update(self):
        try:
            self._results = web.get('%sstreams/%s' % (
                self._base_url, self._name), headers=self._header_info)
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            LOGGER.warning(log.formag("Bad Json loaded from twitch.tv"))
            LOGGER.warning("Raw data is:")
            LOGGER.warning(self._results)
            raise
        if 'error' in self._form_j:
            raise ValueError('%s %s %s' % (
                self._form_j['error'],
                self._form_j['status'],
                self._form_j['message']))
        for s in self._form_j:
            self._settings[s] = self._form_j[s]
        self._form_j = None  # cleanup
        # If stream is populated with data, then stream is live
        if bool(self._live) ^ bool(self._settings['stream']):
            self._live = bool(self._settings['stream'])
            self._last_update = time.time()


class StreamFactory(object):
    def newStream(self, channel, service, alias=None):
        # TODO catch exceptions from object instantiations
        if service == 'twitch.tv':
            return twitchtv(channel, alias)
        elif service == 'livestream.com':
            return livestream(channel, alias)
        elif service == 'youtube.com':
            return youtube(channel, alias)
        elif service == 'ustream.tv':
            return ustream(channel, alias)
        elif service == 'picarto.tv':
            return picarto(channel, alias)
        else:
            return None


def configure(config):
    '''
    | [streams] | example | purpose |
    | --------- | ------- | ------- |
    | stream_help_file_path | /home/willie/.modules/help.html | Absolute path to HTML file to be displayed for help. |
    | stream_help_file_url | http://your.domain.com/help.html | URL pointing to the hosted help page. |
    | stream_list_template_path | /home/willie/.modules/list.html.template | Absolute path to the HTML template to be used for listing streams. |
    | stream_list_main_dest_path | /home/user/dropbox/main.html | Absolute path to where the bot should write the formatted main list HTML file. |
    | stream_list_feat_dest_path | /home/user/dropbox/featured.html | Absolute path to where the bot should write the formatted featured list HTML file. |
    | stream_list_main_url | http://your.domain.com/main.html | URL pointing to the hosted main list page. |
    | stream_list_feat_url | http://your.domain.com/feat.html | URL pointing to the hosted featured list page. |
    '''
    if config.option('Configure stream files and urls', False):
        config.interactive_add(
            'streams',
            'stream_help_file_path',
            'Absolute path to HTML file to be displayed for help.'
        )
        config.interactive_add(
            'streams',
            'stream_help_file_url',
            'URL pointing to the hosted help page.'
        )
        config.interactive_add(
            'streams',
            'stream_list_template_path',
            'Absolute path to the HTML template to be used for listing streams.'
        )
        config.interactive_add(
            'streams',
            'stream_list_main_dest_path',
            'Absolute path to where the bot should write the formatted main list HTML file.'
        )
        config.interactive_add(
            'streams',
            'stream_list_feat_dest_path',
            'Absolute path to where the bot should write the formatted featured list HTML file.'
        )
        config.interactive_add(
            'streams',
            'stream_list_main_url',
            'URL pointing to the hosted main list page.'
        )
        config.interactive_add(
            'streams',
            'stream_list_feat_url',
            'URL pointing to the hosted featured list page.'
        )


def setup(bot):
    # These globals are necessary because the bot.memory dict won't be
    # available where they are referenced
    global _twitch_client_id
    _twitch_client_id = bot.config.streams.twitch_client_id
    global _youtube_api_key
    _youtube_api_key = bot.config.streams.youtube_api_key
    global _ustream_dev_key
    _ustream_dev_key = bot.config.streams.ustream_dev_key
    bot.memory['streamSet'] = {}
    bot.memory['streamSet']['help_file_source'] = bot.config.streams.stream_help_file_source
    bot.memory['streamSet']['help_file_dest'] = '%shelp.html' % bot.config.general.hosted_path
    bot.memory['streamSet']['help_file_url'] = '%shelp.html' % bot.config.general.hosted_domain
    bot.memory['streamSet']['list_template_path'] = bot.config.streams.stream_list_template_path
    bot.memory['streamSet']['list_main_dest_path'] = '%slist.html' % bot.config.general.hosted_path
    bot.memory['streamSet']['list_feat_dest_path'] = '%sfeatured.html' % bot.config.general.hosted_path
    bot.memory['streamSet']['list_main_url'] = '%slist.html' % bot.config.general.hosted_domain
    bot.memory['streamSet']['list_feat_url'] = '%sfeatured.html' % bot.config.general.hosted_domain
    try:
        shutil.copyfile(
            bot.memory['streamSet']['help_file_source'],
            bot.memory['streamSet']['help_file_dest']
        )
    except:
        LOGGER.error(log.format('Unable to copy help file. Check configuration.'), exc_info=True)
        raise
    with open(bot.memory['streamSet']['list_template_path']) as f:
        try:
            bot.memory['streamListT'] = Template(''.join(f.readlines()))
        except:
            LOGGER.error(log.format('Unable to load list template.'), exc_info=True)
            raise

    LOGGER.info(log.format('Starting stream setup, this may take a bit.'))
    # TODO consider making these unique sets
    if 'url_exclude' not in bot.memory:
        bot.memory['url_exclude'] = []
    bot.memory['url_exclude'].extend(_exc_regex)
    if 'streams' not in bot.memory:
        bot.memory['streams'] = []
    if 'feat_streams' not in bot.memory:
        bot.memory['feat_streams'] = []
    if 'streamFac' not in bot.memory:
        bot.memory['streamFac'] = StreamFactory()
    if 'streamLock' not in bot.memory:
        bot.memory['streamLock'] = threading.Lock()
    if 'streamSubs' not in bot.memory:
        bot.memory['streamSubs'] = {}
    if 'streamMsg' not in bot.memory:
        bot.memory['streamMsg'] = {}

    # database stuff
    with bot.memory['streamLock']:
        dbcon = bot.db.connect()  # sqlite3 connection
        cur = dbcon.cursor()
        # If our tables don't exist, create them
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS streams
                           (channel text, service text,
                           m_nsfw int, alias text)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS feat_streams
                           (channel text, service text)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS sub_streams
                           (channel text, service text, nick text)''')
            dbcon.commit()

            # TODO Remove this on next commit
            # Justin.tv cleanup
            cur.execute("DELETE FROM STREAMS WHERE SERVICE = 'justin.tv'")
            cur.execute("DELETE FROM SUB_STREAMS WHERE SERVICE = 'justin.tv'")
            cur.execute("DELETE FROM FEAT_STREAMS WHERE SERVICE = 'justin.tv'")
            dbcon.commit()
        finally:
            cur.close()
            dbcon.close()
    if not bot.memory['streams']:
        load_from_db(bot)


@commands('live_reload')
def load_from_db(bot, trigger=None):
    """ADMIN: Reload live streams from database."""
    if trigger and not trigger.owner:
        return
    LOGGER.info(log.format('Reloading from DB'))
    bot.memory['streams'] = []
    bot.memory['feat_streams'] = []
    dbcon = bot.db.connect()  # sqlite3 connection
    cur = dbcon.cursor()
    try:
        cur.execute('SELECT channel, service, m_nsfw, alias  FROM streams')
        stream_rows = cur.fetchall()
        cur.execute('SELECT channel, service FROM feat_streams')
        feat_rows = cur.fetchall()
        cur.execute('SELECT channel, service, nick FROM sub_streams')
        sub_rows = cur.fetchall()
    finally:
        cur.close()
        dbcon.close()
    for c, s, n, a in stream_rows:
        time.sleep(0.25)
        try:
            bot.memory['streams'].append(
                bot.memory['streamFac'].newStream(c, s, a))
        except:
            LOGGER.error(log.format('Failed to initialize livestream, perhaps due to it being deactivated: Channel=%s, Service=%s, Alias=%s'), c, s, a, exc_info=True)
        if n:
            nsfw(bot, 'nsfw', (c, s), quiet=True)
    for c, s in feat_rows:
        feature(bot, 'feature', (c, s), quiet=True)
    for c, s, n in sub_rows:
        subscribe(bot, 'subscribe', (c, s), Identifier(n), quiet=True)
    LOGGER.info(log.format('Done.'))


def alias(bot, switch, channel, value=None):
    assert isinstance(channel, str) or type(channel) is tuple
    try:
        c, s = parse_service(channel)
    except TypeError:
        bot.say('Bad url or channel/service pair. See !help services.')
        return
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    with bot.memory['streamLock']:
        if switch == 'alias':
            i = None
            for i in [a for a in bot.memory['streams']
                      if a.name == c and a.service == s]:
                i.alias = value
                try:
                    cur.execute('''UPDATE streams
                                    SET alias = ?
                                    WHERE channel = ?
                                    AND service = ?
                                    ''', (value, c, s))
                    dbcon.commit()
                finally:
                    cur.close()
                    dbcon.close()
                bot.say('Set alias for %s to %s.' % (c, value))
                return
            else:
                bot.say("I don't have that stream.")
        elif switch == 'unalias':
            i = None
            for i in [a for a in bot.memory['streams']
                      if a.name == c and a.service == s]:
                if i.alias:
                    del i.alias
                    try:
                        cur.execute('''UPDATE streams
                                        SET alias = NULL
                                        WHERE channel = ?
                                        AND service = ?
                                        ''', (c, s))
                        dbcon.commit()
                    finally:
                        cur.close()
                        dbcon.close()
                    bot.say('Removed alias for %s.' % c)
                    return
                else:
                    bot.say("That doesn't have an alias.")
                    return
            else:
                bot.say("I don't have that stream.")
        else:
            bot.say("Uh, that wasn't supposed to happen.")
            bot.say("!tell tdreyer1 HEEEEEEEEEEELLLLLLP!")


def nsfw(bot, switch, channel, quiet=None):
    assert isinstance(channel, str) or type(channel) is tuple
    try:
        c, s = parse_service(channel)
    except TypeError:
        msg = 'Bad url or channel/service pair. See !help services.'
        if not quiet:
            bot.say(msg)
        else:
            LOGGER.info(log.format(msg))
        return
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    with bot.memory['streamLock']:
        if switch == 'nsfw':
            i = None
            for i in [a for a in bot.memory['streams']
                      if a.name == c and a.service == s]:
                i.m_nsfw = True
                try:
                    cur.execute('''UPDATE streams
                                    SET m_nsfw = 1
                                    WHERE channel = ?
                                    AND service = ?
                                    ''', (c, s))
                    dbcon.commit()
                finally:
                    cur.close()
                    dbcon.close()
                msg = 'Set NSFW tag for %s.' % c
                if not quiet:
                    bot.say(msg)
                else:
                    LOGGER.info(log.format(msg))
                return

            else:
                msg = "I don't have that stream."
                if not quiet:
                    bot.say(msg)
                else:
                    LOGGER.info(log.format(msg))
        elif switch == 'unnsfw':
            i = None
            for i in [a for a in bot.memory['streams']
                      if a.name == c and a.service == s]:
                if i.m_nsfw:
                    del i.m_nsfw
                    try:
                        cur.execute('''SELECT COUNT(*) FROM streams
                                    WHERE channel = ?
                                    AND service = ?
                                    AND m_nsfw = 1
                                    ''', (c, s))
                        if cur.fetchone():
                            cur.execute('''UPDATE streams
                                        SET m_nsfw = 0
                                        WHERE channel = ?
                                        AND service = ?
                                        ''', (c, s))
                        dbcon.commit()
                    finally:
                        cur.close()
                        dbcon.close()
                    msg = 'Removed NSFW tag for %s.' % c
                    if not quiet:
                        bot.say(msg)
                    else:
                        LOGGER.info(log.format(msg))
                    return
                else:
                    msg = "That doesn't have a NSFW tag."
                    if not quiet:
                        bot.say(msg)
                    else:
                        LOGGER.info(log.format(msg))
                    return
            else:
                msg = "I don't have that stream."
                if not quiet:
                    bot.say(msg)
                else:
                    LOGGER.info(log.format(msg))
        else:
            msg = "Uh oh, something broke..."
            if not quiet:
                bot.say(msg)
            else:
                LOGGER.error(log.format(msg))


def more_help(bot, trigger):
    bot.reply('For detailed help, see %s' %
              bot.memory['streamSet']['help_file_url'])


@commands('streams')
def streams_alias(bot, trigger):
    '''Lists live streams.'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    list_streams(bot, 'live')


@commands('live')
def sceencasting(bot, trigger):
    '''Manage various livestreams from multiple services.
 Usage: !live [list/add/del/[un]alias/[un]nsfw/[un]subscribe/]
 [options] | See '!live help' for detailed usage.'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    if len(trigger.args[1].split()) == 1:  # E.G. "!live"
        list_streams(bot, 'live')
        return
    if len(trigger.args[1].split()) == 2:  # E.G. "!stream url"
        arg1 = trigger.args[1].split()[1].lower()
        if arg1 == 'list':
            list_streams(bot, nick=Identifier(trigger.nick))
            return
        if arg1 == 'stats':
            stats(bot)
            return
        if arg1 == 'help':
            more_help(bot, trigger)
            return
        else:
            add_stream(bot, arg1)
            return
    elif len(trigger.args[1].split()) == 3:  # E.G. "!stream add URL"
        arg1 = trigger.args[1].split()[1].lower()
        arg2 = trigger.args[1].split()[2].lower()
        if arg1 == 'add':
            add_stream(bot, arg2)
            return
        elif arg1 == 'del':
            remove_stream(bot, arg2)
            return
        elif arg1 == 'subscribe' or arg1 == 'unsubscribe':
            subscribe(bot, arg1, arg2, Identifier(trigger.nick))
            return
        elif arg1 == 'feature' or arg1 == 'unfeature':
            if trigger.admin:
                feature(bot, arg1, arg2)
                return
            else:
                bot.reply("Sorry, that's an admin only command.")
                return
        elif arg1 == 'list':
            list_streams(bot, arg2, Identifier(trigger.nick))
            return
        elif arg1 == 'info':
            info(bot, arg2)
            return
        elif arg1 == 'unalias':
            alias(bot, arg1, arg2)
            return
        elif arg1 == 'nsfw' or arg1 == 'unnsfw':
            nsfw(bot, arg1, arg2)
            return
    elif len(trigger.args[1].split()) == 4:  # E.G. "!stream add user service"
        arg1 = trigger.args[1].split()[1].lower()
        arg2 = trigger.args[1].split()[2].lower()
        arg3 = trigger.args[1].split()[3].lower()
        if arg1 == 'add':
            add_stream(bot, (arg2, arg3))
            return
        elif arg1 == 'del':
            remove_stream(bot, (arg2, arg3))
            return
        elif arg1 == 'subscribe' or arg1 == 'unsubscribe':
            subscribe(bot, arg1, (arg2, arg3), Identifier(trigger.nick))
            return
        elif arg1 == 'feature' or arg1 == 'unfeature':
            if trigger.admin:
                feature(bot, arg1, (arg2, arg3))
                return
            else:
                bot.reply("Sorry, that's an admin only command.")
                return
        elif arg1 == 'list':
            list_streams(bot, arg2, Identifier(trigger.nick))
            return
        elif arg1 == 'info':
            info(bot, (arg2, arg3))
            return
        elif arg1 == 'alias':
            alias(bot, arg1, arg2, arg3)
            return
        elif arg1 == 'unalias':
            alias(bot, arg1, (arg2, arg3))
            return
        elif arg1 == 'nsfw' or arg1 == 'unnsfw':
            nsfw(bot, arg1, (arg2, arg3))
            return
    elif len(trigger.args[1].split()) == 5:  # E.G. "!stream add user service"
        arg1 = trigger.args[1].split()[1].lower()
        arg2 = trigger.args[1].split()[2].lower()
        arg3 = trigger.args[1].split()[3].lower()
        arg4 = trigger.args[1].split()[4].lower()
        if arg1 == 'alias':
            alias(bot, arg1, (arg2, arg3), arg4)
            return

    # We either got nothing, or too much
    bot.reply("I don't understand that, try '!help live' for info.")


def parse_service(service):
    '''Takes a url string or tuple and returns (chan, service)'''
    assert isinstance(service, str) or type(service) is tuple
    if type(service) is tuple:
        if service[0] in _services:
            return (service[1], service[0])
        if service[1] in _services:
            return service
        else:
            return None
    else:
        if _re_ttv.search(service):
            return (_re_ttv.findall(service)[0], 'twitch.tv')
        elif _re_ls.search(service):
            return (_re_ls.findall(service)[0], 'livestream.com')
        elif _re_yt.search(service):
            return (_re_yt.findall(service)[0][-1], 'youtube.com')
        elif _re_us.search(service):
            return (_re_us.findall(service)[-1][-1], 'ustream.tv')
        elif _re_pic.search(service):
            return (_re_pic.findall(service)[0], 'picarto.tv')
        else:
            return None


def add_stream(bot, user):
    assert isinstance(user, str) or type(user) is tuple

    try:
        u, s = parse_service(user)
    except TypeError:
        bot.say('Bad url or channel/service pair. See !help services.')
        return
    if [a for a in bot.memory['streams'] if a.name == u and a.service == s]:
        bot.reply('I already have that one.')
        return
    else:
        # TODO may need a try block here
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        with bot.memory['streamLock']:
            try:
                bot.memory['streams'].append(
                    bot.memory['streamFac'].newStream(u, s))
            except ValueError as txt:
                if str(txt) == '400 Bad Request':
                    bot.reply('Oops, I did something bad so that did not ' +
                              'work.')
                    bot.say('!tell tdreyer1 FIX IT FIX IT FIX IT FIX IT!')
                    return
                elif str(txt) == '404 Not Found':
                    bot.reply('Channel not found.')
                    return
                elif str(txt) == '500 Internal Server Error':
                    bot.reply('Service returned internal server error, try' +
                              ' again later.')
                    return
                # Twitch.tv - user does not exist
                elif str(txt).startswith('404 Not Found: Channel'):
                    bot.reply('Channel not found.')
                    return
                else:
                    bot.reply('There was an unknown error, check your ' +
                              'spelling and try again later')
                    LOGGER.info(log.format(txt))
                    return
            except timeout as txt:
                LOGGER.info(log.format(txt))
                bot.reply('Oops, the request to the service timed out! ' +
                          'Try again later.')
                return
            try:
                cur.execute('''SELECT COUNT(*) FROM streams
                               WHERE channel = ?
                               AND service = ?''', (u, s))
                if cur.fetchone()[0] == 0:
                    LOGGER.info(log.format('ADD: count was != 0'))
                    cur.execute('''INSERT INTO streams (channel, service)
                                   VALUES (?, ?)''', (u, s))
                    dbcon.commit()
            finally:
                cur.close()
                dbcon.close()
        bot.say('added stream')


def list_streams(bot, arg=None, nick=None):
    _tmp_list = []

    def format_stream(st):
        if st.alias:
            name = '%s on %s' % (st.alias, st.service)
        else:
            name = st
        nsfw = ''
        if st.nsfw or st.m_nsfw:
            nsfw = '[%s] ' % colors.colorize('NSFW', ['red'], ['b'])
        live = ''
        if st.live:
            live = '[%s] ' % colors.colorize('LIVE', ['green'], ['b'])
        return '%s%s%s [ %s ]' % (
            nsfw,
            live,
            colors.colorize(str(name), ['purple']),
            colors.colorize(st.url, ['blue']))

    if arg == 'subscribed' or arg == 'subscriptions':
        # Private subscriptions should be PM'd, even if many
        assert isinstance(nick, Identifier)
        if len(bot.memory['streamSubs']) == 0:
            bot.say("You aren't subscribed to anything.")
            return
        s = None
        bot.reply('Sending you the list in pm.')
        for s in [a for a in bot.memory['streamSubs']
                  for n in bot.memory['streamSubs'][a] if n == nick]:
            _tmp_list.append(format_stream(s))
        if _tmp_list:
            _tmp_list.sort()
            for i in _tmp_list:
                bot.msg(nick, i)
            return
        bot.say("You aren't subscribed to anything.")
    elif arg == 'live' or arg == 'streaming':
        # Should be few enough streaming at any one time, just say in chat
        s = None
        for s in [a for a in bot.memory['streams'] if a.live]:
            _tmp_list.append(format_stream(s))
        if _tmp_list:
            _tmp_list.sort()
            for i in _tmp_list:
                bot.say(i)
            return
        bot.say("No one is streaming right now.")
    elif not arg:
        # Too many to say in chat, link to HTML list
        if len(bot.memory['streams']) == 0:
            bot.say("I've got nothing.")
        else:
            bot.say("The current list is up at %s" %
                    bot.memory['streamSet']['list_main_url'])
        return
    elif arg == 'featured':
        if len(bot.memory['feat_streams']) == 0:
            bot.say("I've got nothing.")
        else:
            bot.say("The current list is up at %s" %
                    bot.memory['streamSet']['list_feat_url'])
        return
        for i in bot.memory['feat_streams']:
            bot.msg(nick, format_stream(i))
        return
    else:
        bot.say("I don't understand what you want me to list!")


def publish_lists(bot, trigger=None):
    def format_html(st):
        def wrap_link(link):
            return '<a href = "%s">%s</a>' % (link, link)

        if st.alias:
            name = '%s on %s' % (st.alias, st.service)
        else:
            name = st
        nsfw = ''
        if st.nsfw or st.m_nsfw:
            nsfw = "<span id='nsfw'>[NSFW]</span> "
        live = ''
        if st.live:
            live = "<span id='live'>[LIVE]</span> "
        return '%s%s%s \n[ %s ]<br />' % (nsfw, live, name, wrap_link(st.url))

    try:
        with open(bot.memory['streamSet']['list_main_dest_path'], 'r') as f:
            previous_full_list = ''.join(f.readlines())
    except IOError:
        previous_full_list = ''
        LOGGER.warning(log.format('IO error grabbing "list_main_dest_path" file contents. File may not exist yet'))

    try:
        with open(bot.memory['streamSet']['list_feat_dest_path'], 'r') as f:
            previous_feat_list = ''.join(f.readlines())
    except IOError:
        previous_feat_list = ''
        LOGGER.info(log.format('IO error grabbing "list_feat_dest_path" file contents. File may not exist yet'))

    # Generate full list HTML
    live_list = []
    dead_list = []
    for i in [a for a in bot.memory['streams'] if a.live]:
        live_list.append(format_html(i))
    for i in [a for a in bot.memory['streams'] if not a.live]:
        dead_list.append(format_html(i))
    if not live_list:
        live_list = ["No currently streaming channels found.<br />"]
    if not dead_list:
        dead_list = ["No other channels found.<br />"]
    live_list.sort()
    dead_list.sort()
    contents = bot.memory['streamListT'].substitute(
        title='Full Stream List',
        live='\n'.join(live_list),
        dead='\n'.join(dead_list))
    # Don't clobber the HDD
    if previous_full_list != contents:
        LOGGER.info(log.format('Found change in full list html file.'))
        with open(bot.memory['streamSet']['list_main_dest_path'], 'w') as f:
            f.write(contents)
    # Generate featured list HTML
    live_list = []
    dead_list = []
    for i in [a for a in bot.memory['feat_streams'] if a.live]:
        live_list.append(format_html(i))
    for i in [a for a in bot.memory['feat_streams'] if not a.live]:
        dead_list.append(format_html(i))
    if not live_list:
        live_list = ["No currently streaming channels found.<br />"]
    if not dead_list:
        dead_list = ["No other channels found.<br />"]
    live_list.sort()
    dead_list.sort()
    contents = bot.memory['streamListT'].substitute(
        title='Featured Stream List',
        live='\n'.join(live_list),
        dead='\n'.join(dead_list))
    # Don't clobber the HDD
    if previous_feat_list != contents:
        LOGGER.info(log.format('Found change in featured list html file.'))
        with open(bot.memory['streamSet']['list_feat_dest_path'], 'w') as f:
            f.write(contents)
    return


@commands('services')
def services(bot, trigger):
    '''Proper !live input includes a URL by itself (e.g. http://twitch.tv/tdreyer1)
 or a channel name / service name pair (e.g. tdreyer1 twitch.tv). Accepted
 service names are livestream.com, twitch.tv, ustream.tv, picarto.tv, and youtube.com'''
    bot.say(__doc__.strip())
    return


def remove_stream(bot, user):
    assert isinstance(user, str) or type(user) is tuple

    try:
        u, s = parse_service(user)
    except TypeError:
        bot.say('Bad url or channel/service pair. See !help services.')
        return
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    with bot.memory['streamLock']:
        for i in [a for a in bot.memory['streams']
                  if a.name.lower() == u.lower() and a.service == s]:
            try:
                cur.execute('''DELETE FROM feat_streams
                               WHERE lower(channel) = lower(?)
                               AND service = ?''', (u, s))
                cur.execute('''DELETE FROM streams
                               WHERE lower(channel) = lower(?)
                               AND service = ?''', (u, s))
                cur.execute('''DELETE FROM sub_streams
                               WHERE lower(channel) = lower(?)
                               and service = ?''', (u, s))
                dbcon.commit()
            finally:
                cur.close()
                dbcon.close()
            try:
                bot.memory['feat_streams'].remove(i)
            except ValueError:
                # Stream is not in the featured list
                pass
            try:
                del bot.memory['streamSubs'][i]
            except KeyError:
                # Stream is not in the subscription list
                pass
            bot.memory['streams'].remove(i)
            bot.say('Stream removed.')
            return
        else:
            bot.say("I don't have that stream.")


@commands('update', 'reload', 'refresh')
def update_streams(bot, trigger):
    '''Force update of live streams. Admin only.'''
    if not trigger.owner:
        return
    with bot.memory['streamLock']:
        bot.reply('updating streams')
        for i in bot.memory['streams']:
            i.update()
            time.sleep(0.25)
        bot.reply('Streams updated')


def feature(bot, switch, channel, quiet=False):
    assert isinstance(channel, str) or type(channel) is tuple
    try:
        u, s = parse_service(channel)
    except TypeError:
        msg = 'Bad url or channel/service pair. See !help services.'
        if not quiet:
            bot.say(msg)
        else:
            LOGGER.info(log.format(msg))
        return
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    with bot.memory['streamLock']:
        if switch == 'feature':
            for i in [a for a in bot.memory['streams']
                      if a.name.lower() == u.lower() and a.service == s]:
                if i in bot.memory['feat_streams']:
                    msg = "That's already featured!"
                    if not quiet:
                        bot.say(msg)
                    else:
                        LOGGER.info(log.format(msg))
                    return
                else:
                    try:
                        cur.execute('''SELECT COUNT(*) FROM feat_streams
                                       WHERE lower(channel) = lower(?)
                                       AND service = ?''', (u, s))
                        if cur.fetchone()[0] == 0:
                            cur.execute('''INSERT INTO feat_streams
                                           (channel, service)
                                           VALUES (?, ?)''', (u, s))
                            dbcon.commit()
                    finally:
                        cur.close()
                        dbcon.close()
                    bot.memory['feat_streams'].append(i)
                    msg = 'Stream featured.'
                    if not quiet:
                        bot.say(msg)
                    else:
                        LOGGER.info(log.format(msg))
                    return
            msg = "Not a channel or that channel hasn't been added yet!"
            if not quiet:
                bot.say(msg)
            else:
                LOGGER.info(log.format(msg))
            return
        elif switch == 'unfeature':
            for i in [a for a in bot.memory['feat_streams']
                      if a.name.lower() == u.lower() and a.service == s]:
                try:
                    cur.execute('''DELETE FROM feat_streams
                                   WHERE lower(channel) = lower(?)
                                   AND service = ?''', (u, s))
                    dbcon.commit()
                finally:
                    cur.close()
                    dbcon.close()
                bot.memory['feat_streams'].remove(i)
                msg = 'Stream unfeatured.'
                if not quiet:
                    bot.say(msg)
                else:
                    LOGGER.info(log.format(msg))
                return
            msg = "Not a channel or that channel hasn't been added yet!"
            if not quiet:
                bot.say(msg)
            else:
                LOGGER.info(log.format(msg))
            return
        else:
            msg = "Oh shit, I don't know what just happened."
            if not quiet:
                bot.reply(msg)
            else:
                LOGGER.info(log.format(msg))


def subscribe(bot, switch, channel, nick, quiet=False):
    assert isinstance(channel, str) or type(channel) is tuple
    assert isinstance(switch, str)
    assert isinstance(nick, Identifier)
    try:
        u, s = parse_service(channel)
    except TypeError:
        msg = 'Bad url or channel/service pair. See !help services.'
        if not quiet:
            bot.say(msg)
        else:
            LOGGER.info(log.format(msg))
        return
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    with bot.memory['streamLock']:
        for i in [a for a in bot.memory['streams']
                  if a.name.lower() == u.lower() and a.service == s]:
            if switch == 'subscribe':
                if i not in bot.memory['streamSubs']:
                    bot.memory['streamSubs'][i] = []
                if nick not in bot.memory['streamSubs'][i]:
                    try:
                        cur.execute('''SELECT COUNT(*) FROM sub_streams
                                    WHERE lower(channel) = lower(?)
                                    AND service = ?''', (u, s))
                        if cur.fetchone()[0] == 0:
                            cur.execute('''INSERT INTO sub_streams
                                        (channel, service, nick)
                                        VALUES (?, ?, ?)''', (u, s, nick))
                            dbcon.commit()
                    finally:
                        cur.close()
                        dbcon.commit()
                    bot.memory['streamSubs'][i].append(nick)
                    msg = 'Subscription added.'
                    if not quiet:
                        bot.reply(msg)
                    else:
                        LOGGER.info(log.format(msg))
                    return
                else:
                    msg = "You're already subscribed to that channel!"
                    if not quiet:
                        bot.reply(msg)
                    else:
                        LOGGER.info(log.format(msg))
            elif switch == 'unsubscribe':
                if i in bot.memory['streamSubs']:
                    if nick in bot.memory['streamSubs'][i]:
                        try:
                            cur.execute('''DELETE FROM sub_streams
                                           WHERE lower(channel) = lower(?)
                                           AND service = ?
                                           AND nick = ?''', (u, s, nick))
                            dbcon.commit()
                        finally:
                            cur.close()
                            dbcon.close()
                        bot.memory['streamSubs'][i].remove(nick)
                        msg = 'Subscription removed.'
                        if not quiet:
                            bot.reply(msg)
                        else:
                            LOGGER.info(log.format(msg))
                        return
                msg = "You weren't subscribed to that or that doesn't exist."
                if not quiet:
                    bot.reply(msg)
                else:
                    LOGGER.info(log.format(msg))
            else:
                msg = "Oh shit, I don't know what just happened."
                if not quiet:
                    bot.reply(msg)
                else:
                    LOGGER.info(log.format(msg))


@interval(47)
def announcer(bot):
    def whisper(nick, strm):
        if strm.alias:
            bot.msg(nick, '%s has started streaming at %s' % (strm.alias, strm.url))
        else:
            bot.msg(nick, '%s has started streaming at %s' % (strm.name, strm.url))

    def announce(chan, strm):
        if strm.alias:
            bot.msg(chan, 'Hey everyone, %s has started streaming at %s' % (strm.alias, strm.url))
        else:
            bot.msg(chan, 'Hey everyone, %s has started streaming at %s' % (strm.name, strm.url))

    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    LOGGER.debug(log.format('Announcer waking up'))
    publish_lists(bot)
    # IMPORTANT _msg_interval must be larger than _announce_interval
    # Time in which to consider streams having been updated recently
    _announce_interval = 10 * 60
    # Min time between messages to channel or user
    _msg_interval = 20 * 60

    with bot.memory['streamLock']:
        for s in [a for a in bot.memory['streamSubs']
                  if a.live and a.updated > time.time() - _announce_interval]:
            for n in bot.memory['streamSubs'][s]:
                if n not in bot.memory['streamMsg']:
                    bot.memory['streamMsg'][n] = {}
                if s not in bot.memory['streamMsg'][n]:
                    # TODO may error if nick isn't on server
                    whisper(n, s)
                    bot.memory['streamMsg'][n][s] = time.time()
                elif bot.memory['streamMsg'][n][s] < \
                        time.time() - _msg_interval:
                    # TODO may error if nick isn't on server
                    whisper(n, s)
                    bot.memory['streamMsg'][n][s] = time.time()
                else:
                    # Nick was msg'd about stream too recently. The stream may
                    # be experiencing trouble so we don't want to spam them
                    pass
        for s in [a for a in bot.memory['feat_streams']
                  if a.live and a.updated > time.time() - _announce_interval]:
            for n in [x for x in bot.channels if x in _include]:
                if n not in bot.memory['streamMsg']:
                    bot.memory['streamMsg'][n] = {}
                if s not in bot.memory['streamMsg'][n]:
                    announce(n, s)
                    bot.memory['streamMsg'][n][s] = time.time()
                elif bot.memory['streamMsg'][n][s] < \
                        time.time() - _msg_interval:
                    announce(n, s)
                    bot.memory['streamMsg'][n][s] = time.time()
                else:
                    # Chan was msg'd about stream too recently. The stream may
                    # be experiencing trouble so we don't want to spam
                    pass
    LOGGER.debug(log.format('Announcer sleeping'))


# Livestream limits access to the following limits
#    10 requests per second
#    100 requests per minutes ( ~1 / 2sec )
#    1000 requests per hour ( ~1 / 3sec )
#    10000 requests per day ( ~1 / 9sec )
@interval(223)
def livestream_updater(bot):
    LOGGER.debug(log.format('Starting livestream.com updater.'))
    now = time.time()
    for s in [i for i in bot.memory['streams'] if i.service == 'livestream.com']:
        try:
            # TODO handle timeout, misc exceptions
            s.update()
        except ValueError:
            pass
        time.sleep(0.25)
    LOGGER.debug(log.format('livestream.com updater complete in %s seconds.'), (time.time() - now))


@interval(227)
def twitchtv_updater(bot):
    LOGGER.debug(log.format('Starting twitch.tv updater.'))
    now = time.time()
    for s in [i for i in bot.memory['streams'] if i.service == 'twitch.tv']:
        # TODO handle timeout, misc exceptions
        s.update()
        time.sleep(0.25)
    LOGGER.debug(log.format('twitch.tv updater complete in %s seconds.'), (time.time() - now))


@interval(229)
def youtube_updater(bot):
    LOGGER.debug(log.format('Starting youtube.com updater.'))
    now = time.time()
    for s in [i for i in bot.memory['streams'] if i.service == 'youtube.com']:
        s.update()
        time.sleep(0.25)
    LOGGER.debug(log.format('youtube.com updater complete in %s seconds.'), (time.time() - now))


@interval(239)
def ustream_updater(bot):
    LOGGER.debug(log.format('Starting ustream.tv updater.'))
    now = time.time()
    # channel_list = [i.name for i in bot.memory['streams'] if i.service == 'ustream.tv']
    # if len(channel_list) == 0:
    #    return
    # Range will be length mod 10
    # for i in channel_list:
    for s in [i for i in bot.memory['streams'] if i.service == 'ustream.tv']:
        s.update()
        time.sleep(0.25)
        '''
    for i in range(len(channel_list) / 10 + 1):
        # TODO handle timeout, misc exceptions
        update ';'.join stuff

    for s in [i for i in bot.memory['streams'] if i.service == 'ustream.tv']:
        # TODO handle timeout, misc exceptions
        s.update()
        time.sleep(0.25)
        '''
    LOGGER.debug(log.format('ustream.tv updater complete in %s seconds.'), (time.time() - now))


@interval(161)
def picarto_updater(bot):
    LOGGER.debug(log.format('Starting picarto.tv updater.'))
    try:
        now = time.time()
        for s in [i for i in bot.memory['streams'] if i.service == 'picarto.tv']:
            # TODO handle timeout, misc exceptions
            s.update()
            time.sleep(0.25)
        LOGGER.debug(log.format('picarto.tv updater complete in %s seconds.'), (time.time() - now))
    except:
        LOGGER.error(log.format('Unhandled exception in the picarto updater.'), exc_info=True)


def info():
    # TODO
    return


def url_watcher():
    # TODO Write function that watches for stream URLs in chat, and post info
    # about them. Don't forget to exclude these from the regular URL watcher
    return


def stats(bot):
    # TODO Need a function that will report stats like number of streams,
    # number of featured, number of subs, steams by service
    bot.say('I am tracking %s streams, %s of which are featured.' %
            (len(bot.memory['streams']), len(bot.memory['feat_streams'])))
    bot.say(('There are %s from livestream.com, '
             '%s from twitch.tv, %s from youtube.com, %s '
             'from ustream.tv, and %s from picarto.tv.') % (
            len([i for i in bot.memory['streams']
                if i.service == 'livestream.com']),
            len([i for i in bot.memory['streams']
                if i.service == 'twitch.tv']),
            len([i for i in bot.memory['streams']
                if i.service == 'youtube.com']),
            len([i for i in bot.memory['streams']
                if i.service == 'ustream.tv']),
            len([i for i in bot.memory['streams']
                if i.service == 'picarto.tv'])
            ))
    bot.say('There are %s individual subscriptions.' %
            len(bot.memory['streamSubs']))


@commands('db_maint')
def update_database_tables(bot, trigger):
    '''Manual one time database maintance. Don't run this. Admin only.'''
    if not trigger.owner:
        return
    with bot.memory['streamLock']:
        dbcon = bot.db.connect()  # sqlite3 connection
        cur = dbcon.cursor()
        try:
            cur.execute('''update streams set service = 'livestream.com'
                        where service = 'livestream' ''')
        finally:
            cur.close()
            dbcon.close()


if __name__ == "__main__":
    print(__doc__.strip())
