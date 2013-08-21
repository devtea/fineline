"""
streams.py - A willie module to track livestreams from popular services
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import json
import re
import time
import threading
import imp
import shutil
import sys
from socket import timeout
from string import Template

import willie.web as web
from willie.module import commands, interval
from willie.tools import Nick
# Bot framework is stupid about importing, so we need to override so that
# the colors module is always available for import.
try:
    import colors
except:
    try:
        fp, pathname, description = imp.find_module('colors',
                                                    ['./.willie/modules/']
                                                    )
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
    finally:
        if fp:
            fp.close()

_exc_regex = []
_twitch_client_id = None
_re_jtv = re.compile('(?<=justin\.tv/)[^/(){}[\]]+')
_exc_regex.append(re.compile('justin\.tv/'))
_re_ttv = re.compile('(?<=twitch\.tv/)[^/(){}[\]]+')
_exc_regex.append(re.compile('twitch\.tv/'))
_re_ls = re.compile('(?<=livestream\.com/)[^/(){}[\]]+')
_exc_regex.append(re.compile('livestream\.com/'))
_re_us = re.compile('(?<=ustream\.tv/)[^/(){}[\]]+')
_exc_regex.append(re.compile('ustream\.tv/'))
_re_yt = re.compile('(?<=youtube\.com/)[^/(){}[\]]+')
_exc_regex.append(re.compile('youtube\.com/'))
#_url_finder = re.compile(r'(?u)(%s?(?:http|https)(?:://\S+))')
_services = ['justin.tv', 'twitch.tv', 'livestream.com', 'youtube.com',
             'ustream.tv']
_SUB = ('?',)  # This will be replaced in setup()


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
        return u'%s on %s' % (self.name, self.service)

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
        assert isinstance(value, basestring)
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


class justintv(stream):
    # http://www.justin.tv/p/api
    _base_url = 'http://api.justin.tv/api/'
    _service = 'justin.tv'
    _last_update = time.time()
    #_header_info = ''

    def __init__(self, name, alias=None):
        super(justintv, self).__init__(name, alias)
        self.update()

    def update(self):
        # Update stream info - first grab chan, then try to grab stream
        # Update channel info
        try:
            self._results = web.get(u'%schannel/show/%s.json' % (
                self._base_url, self._name))
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            print "Bad Json loaded from justin.tv"
            raise
        except IndexError:
            raise
        except TypeError:
            raise
        #print 'got json'
        #print json.dumps(self._form_j, indent=4)
        try:
            raise ValueError(self._form_j['error'])
        except KeyError:
            pass
        for s in self._form_j:
            self._settings[s] = self._form_j[s]
        self._form_j = None  # cleanup

        # Update stream info if available
        try:
            self._results = web.get(u'%sstream/list.json?channel=%s' % (
                self._base_url, self._name))
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            print "Bad Json loaded from justin.tv"
            print "Raw data is:"
            print self._results
            raise
        except IndexError:
            raise
        except TypeError:
            raise
        if self._form_j:
            # We got results here, it means the stream is live
            if not self._live:
                self._last_update = time.time()
                self._live = True
            try:
                raise ValueError(self._form_j['error'])
            except KeyError:
                # the object has no key 'error' so nothing's wrong
                pass
            except TypeError:
                # The object is probably valid, dict inside list
                pass
            # Load data [{...}]
            for s in self._form_j[0]:
                self._settings[s] = self._form_j[0][s]
        else:
            # No results means stream's not live if self._live:
                self._live = False
                self._last_update = time.time()
        self._form_j = None  # cleanup
        self._url = self._settings['channel_url']
        # NSFW flag is one of ['true', 'false', None]
        if self._settings['mature'] == 'true':
            self._nsfw = True
        else:
            self._nsfw = False


class livestream(stream):
    # http://www.livestream.com/userguide/index.php?title=Channel_API_2.0
    _base_url = '.api.channel.livestream.com/2.0/'
    _service = 'livestream.com'
    _last_update = time.time()
    #_header_info = ''

    def __init__(self, name, alias=None):
        super(livestream, self).__init__(name, alias)
        self._safename = re.sub('_', '-', self._name)
        try:
            self._results = web.get(u'x%sx%sinfo.json' % (
                self._safename, self._base_url))
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            if re.findall('400 Bad Request', self._results):
                print 'Livestream Error: 400 Bad Request'
                raise ValueError('400 Bad Request')
            elif re.findall('404 Not Found', self._results):
                print 'Livestream Error: 404 Not Found'
                raise ValueError('404 Not Found')
            elif re.findall('500 Internal Server Error', self._results):
                print 'Livestream Error: 500 Internal Server Error'
                raise ValueError('500 Internal Server Error')
            else:
                print "Bad Json loaded from livestream.com"
                print "Raw data is:"
                print self._results
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
            self._results = web.get(u'x%sx%slivestatus.json' % (
                self._safename, self._base_url))
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            if re.findall('400 Bad Request', self._results):
                print 'Livestream Error: 400 Bad Request'
                raise ValueError('400 Bad Request')
            elif re.findall('404 Not Found', self._results):
                print 'Livestream Error: 404 Not Found'
                raise ValueError('404 Not Found')
            elif re.findall('500 Internal Server Error', self._results):
                print 'Livestream Error: 500 Internal Server Error'
                raise ValueError('500 Internal Server Error')
            else:
                print "Bad Json loaded from livestream.com"
                print "Raw data is:"
                print self._results
                raise
        for s in self._form_j['channel']:
            self._settings[s] = self._form_j['channel'][s]
        if bool(self._live) ^ bool(self._settings['isLive']):
            self._live = self._settings['isLive']
            self._last_update = time.time()


class ustream(stream):
    pass


class youtube(stream):
    pass


class twitchtv(stream):
    # https://github.com/justintv/twitch-api
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
            self._results = web.get(u'%schannels/%s' % (
                self._base_url, self._name), headers=self._header_info)
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            print "Bad Json loaded from twitch.tv"
            print "Raw data is:"
            print self._results
            raise
        if 'error' in self._form_j:
            raise ValueError('%s %s: %s' % (
                self._form_j['status'],
                self._form_j['error'],
                self._form_j['message']))
        #print 'got json'
        #print json.dumps(self._form_j, indent=4)
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
            self._results = web.get(u'%sstreams/%s' % (
                self._base_url, self._name), headers=self._header_info)
        except timeout:
            raise
        try:
            self._form_j = json.loads(self._results)
        except ValueError:
            print "Bad Json loaded from twitch.tv"
            print "Raw data is:"
            print self._results
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
        if service == 'justin.tv':
            return justintv(channel, alias)
        elif service == 'twitch.tv':
            return twitchtv(channel, alias)
        elif service == 'livestream.com':
            return livestream(channel, alias)
        elif service == 'youtube.com':
            return youtube(channel, alias)
        elif service == 'ustream.tv':
            return ustream(channel, alias)
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
    global _twitch_client_id
    _twitch_client_id = bot.config.streams.twitch_client_id
    bot.memory['streamSet'] = {}
    bot.memory['streamSet']['help_file_source'] = bot.config.streams.stream_help_file_source
    bot.memory['streamSet']['help_file_dest'] = bot.config.streams.stream_help_file_dest
    bot.memory['streamSet']['help_file_url'] = bot.config.streams.stream_help_file_url
    bot.memory['streamSet']['list_template_path'] = bot.config.streams.stream_list_template_path
    bot.memory['streamSet']['list_main_dest_path'] = bot.config.streams.stream_list_main_dest_path
    bot.memory['streamSet']['list_feat_dest_path'] = bot.config.streams.stream_list_feat_dest_path
    bot.memory['streamSet']['list_main_url'] = bot.config.streams.stream_list_main_url
    bot.memory['streamSet']['list_feat_url'] = bot.config.streams.stream_list_feat_url
    try:
        shutil.copyfile(
            bot.memory['streamSet']['help_file_source'],
            bot.memory['streamSet']['help_file_dest']
        )
    except:
        bot.debug(u'streams.py',
                  u'Unable to copy help file. Check configuration.',
                  u'always')
        raise
    with open(bot.memory['streamSet']['list_template_path']) as f:
        try:
            bot.memory['streamListT'] = Template(''.join(f.readlines()))
        except:
            bot.debug(u'streams.py',
                      u'Unable to load list template.',
                      u'always')
            raise

    bot.debug(
        u'streams.py',
        u'Starting stream setup, this may take a bit.',
        'always'
    )
    # TODO consider making these unique sets
    if 'url_exclude' not in bot.memory:
        bot.memory['url_exclude'] = []
    for i in _exc_regex:
        bot.memory['url_exclude'].append(i)
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
    global _SUB
    _SUB = (bot.db.substitution,)
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
        finally:
            cur.close()
            dbcon.close()
    if not bot.memory['streams']:
        load_from_db(bot)


@commands('live_reload')
def load_from_db(bot, trigger=None):
    bot.debug(u'streams.py:reload', u'Reloading from DB', 'verbose')
    if trigger and not trigger.admin:
        return
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
        bot.memory['streams'].append(
            bot.memory['streamFac'].newStream(c, s, a))
        if n:
            nsfw(bot, 'nsfw', (c, s), quiet=True)
    for c, s in feat_rows:
        feature(bot, 'feature', (c, s), quiet=True)
    for c, s, n in sub_rows:
        subscribe(bot, 'subscribe', (c, s), Nick(n), quiet=True)
    bot.debug(u'streams.py:reload', u'Done.', 'verbose')


def alias(bot, switch, channel, value=None):
    assert isinstance(channel, basestring) or type(channel) is tuple
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
                                    SET alias = %s
                                    WHERE channel = %s
                                    AND service = %s
                                    ''' % (_SUB * 3), (value, c, s))
                    dbcon.commit()
                finally:
                    cur.close()
                    dbcon.close()
                bot.say(u'Set alias for %s to %s.' % (c, value))
                return
            else:
                bot.say(u"I don't have that stream.")
        elif switch == 'unalias':
            i = None
            for i in [a for a in bot.memory['streams']
                      if a.name == c and a.service == s]:
                if i.alias:
                    del i.alias
                    try:
                        cur.execute('''UPDATE streams
                                        SET alias = NULL
                                        WHERE channel = %s
                                        AND service = %s
                                        ''' % (_SUB * 2), (c, s))
                        dbcon.commit()
                    finally:
                        cur.close()
                        dbcon.close()
                    bot.say(u'Removed alias for %s.' % c)
                    return
                else:
                    bot.say(u"That doesn't have an alias.")
                    return
            else:
                bot.say(u"I don't have that stream.")
        else:
            bot.say(u"Uh, that wasn't supposed to happen.")
            bot.say(u"!tell tdreyer1 HEEEEEEEEEEELLLLLLP!")


def nsfw(bot, switch, channel, quiet=None):
    assert isinstance(channel, basestring) or type(channel) is tuple
    try:
        c, s = parse_service(channel)
    except TypeError:
        msg = u'Bad url or channel/service pair. See !help services.'
        if not quiet:
            bot.say(msg)
        else:
            bot.debug('streams:load_from_db', msg, 'warning')
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
                                    WHERE channel = %s
                                    AND service = %s
                                    ''' % (_SUB * 2), (c, s))
                    dbcon.commit()
                finally:
                    cur.close()
                    dbcon.close()
                msg = u'Set NSFW tag for %s.' % c
                if not quiet:
                    bot.say(msg)
                else:
                    bot.debug('streams:load_from_db', msg, 'warning')
                return

            else:
                msg = u"I don't have that stream."
                if not quiet:
                    bot.say(msg)
                else:
                    bot.debug('streams:load_from_db', msg, 'warning')
        elif switch == 'unnsfw':
            i = None
            for i in [a for a in bot.memory['streams']
                      if a.name == c and a.service == s]:
                if i.m_nsfw:
                    del i.m_nsfw
                    try:
                        cur.execute('''SELECT COUNT(*) FROM streams
                                    WHERE channel = %s
                                    AND service = %s
                                    AND m_nsfw = 1
                                    ''' % (_SUB * 2), (c, s))
                        if cur.fetchone():
                            cur.execute('''UPDATE streams
                                        SET m_nsfw = 0
                                        WHERE channel = %s
                                        AND service = %s
                                        ''' % (_SUB * 2), (c, s))
                        dbcon.commit()
                    finally:
                        cur.close()
                        dbcon.close()
                    msg = u'Removed NSFW tag for %s.' % c
                    if not quiet:
                        bot.say(msg)
                    else:
                        bot.debug('streams:load_from_db', msg, 'warning')
                    return
                else:
                    msg = u"That doesn't have a NSFW tag."
                    if not quiet:
                        bot.say(msg)
                    else:
                        bot.debug('streams:load_from_db', msg, 'warning')
                    return
            else:
                msg = u"I don't have that stream."
                if not quiet:
                    bot.say(msg)
                else:
                    bot.debug('streams:load_from_db', msg, 'warning')
        else:
            msg = u"Uh oh, that wasn't supposed to happen."
            if not quiet:
                bot.say(msg)
                bot.say(u"!tell tdreyer1 FIIIIIXX MEEEEEEEE!")
            else:
                bot.debug('streams:load_from_db', msg, 'warning')


def more_help(bot, trigger):
    bot.reply(u'For detailed help, see %s' %
              bot.memory['streamSet']['help_file_url'])


@commands('live')
def sceencasting(bot, trigger):
    '''Manage various livestreams from multiple services.
 Usage: !live [list/add/del/[un]alias/[un]nsfw/[un]subscribe/]
 [options] | See '!live help' for detailed usage.'''
    if len(trigger.args[1].split()) == 2:  # E.G. "!stream url"
        arg1 = trigger.args[1].split()[1].lower()
        if arg1 == 'list':
            list_streams(bot, nick=Nick(trigger.nick))
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
            subscribe(bot, arg1, arg2, Nick(trigger.nick))
            return
        elif arg1 == 'feature' or arg1 == 'unfeature':
            if trigger.admin:
                feature(bot, arg1, arg2)
                return
            else:
                bot.reply(u"Sorry, that's an admin only command.")
                return
        elif arg1 == 'list':
            list_streams(bot, arg2, Nick(trigger.nick))
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
            subscribe(bot, arg1, (arg2, arg3), Nick(trigger.nick))
            return
        elif arg1 == 'feature' or arg1 == 'unfeature':
            if trigger.admin:
                feature(bot, arg1, (arg2, arg3))
                return
            else:
                bot.reply(u"Sorry, that's an admin only command.")
                return
        elif arg1 == 'list':
            list_streams(bot, arg2, Nick(trigger.nick))
            return
        elif arg1 == 'info':
            info(bot, (arg2, arg3))
            return
        elif arg1 == 'alias' or arg1 == 'unalias':
            alias(bot, arg1, arg2, arg3)
            return
        elif arg1 == 'nsfw' or arg1 == 'unnsfw':
            nsfw(bot, arg1, (arg2, arg3))
            return
    elif len(trigger.args[1].split()) == 5:  # E.G. "!stream add user service"
        arg1 = trigger.args[1].split()[1].lower()
        arg2 = trigger.args[1].split()[2].lower()
        arg3 = trigger.args[1].split()[3].lower()
        arg4 = trigger.args[1].split()[4].lower()
        if arg1 == 'alias' or arg1 == 'unalias':
            alias(bot, arg1, (arg2, arg3), arg4)
            return

    # We either got nothing, or too much
    bot.reply("I don't understand that, try '!help live' for info.")


def parse_service(service):
    '''Takes a url string or tuple and returns (chan, service)'''
    assert isinstance(service, basestring) or type(service) is tuple
    if type(service) is tuple:
        if service[0] in _services:
            return (service[1], service[0])
        if service[1] in _services:
            return service
        else:
            return None
    else:
        if _re_jtv.search(service):
            return (_re_jtv.findall(service)[0], 'justin.tv')
        elif _re_ttv.search(service):
            return (_re_ttv.findall(service)[0], 'twitch.tv')
        elif _re_ls.search(service):
            return (_re_ls.findall(service)[0], 'livestream.com')
        elif _re_yt.search(service):
            return (_re_ls.findall(service)[0], 'youtube.com')
        elif _re_us.search(service):
            return (_re_ls.findall(service)[0], 'ustream.tv')
        else:
            return None


def add_stream(bot, user):
    assert isinstance(user, basestring) or type(user) is tuple

    try:
        u, s = parse_service(user)
    except TypeError:
        bot.say('Bad url or channel/service pair. See !help services.')
        return
    if [a for a in bot.memory['streams'] if a.name == u and a.service == s]:
        bot.reply(u'I already have that one.')
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
                    bot.reply(u'Oops, I did something bad so that did not ' +
                              u'work.')
                    bot.say('!tell tdreyer1 FIX IT FIX IT FIX IT FIX IT!')
                    return
                elif str(txt) == '404 Not Found':
                    bot.reply(u'Channel not found.')
                    return
                elif str(txt) == '500 Internal Server Error':
                    bot.reply(u'Service returned internal server error, try' +
                              u' again later.')
                    return
                # Twitch.tv - user is a justin.tv user
                elif str(txt).startswith('422 Unprocessable Entity: Channel'):
                    bot.reply(u'That is actually a justin.tv user.')
                    return
                # Twitch.tv - user does not exist
                elif str(txt).startswith('404 Not Found: Channel'):
                    bot.reply(u'Channel not found.')
                    return
                else:
                    bot.reply(u'There was an unknown error, check your ' +
                              u'spelling and try again later')
                    bot.debug(u'streams.py', txt, 'warnings')
                    return
            try:
                cur.execute('''SELECT COUNT(*) FROM streams
                               WHERE channel = %s
                               AND service = %s''' % (_SUB * 2), (u, s))
                if cur.fetchone()[0] == 0:
                    bot.debug(u'streams.py',
                              u'ADD: count was != 0',
                              u'verbose')
                    cur.execute('''INSERT INTO streams (channel, service)
                                   VALUES (%s, %s)''' % (_SUB * 2), (u, s))
                    dbcon.commit()
            finally:
                cur.close()
                dbcon.close()
        bot.say('added stream')


def list_streams(bot, arg=None, nick=None):
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
        return '%s%s%s [ %s ]' % (nsfw, live, name, colors.colorize(st.url,
                                                                    ['blue']))

    # TODO add option to list only live streams
    if arg == 'subscribed' or arg == 'subscriptions':
        #Private subscriptions should be PM'd, even if many
        assert isinstance(nick, Nick)
        if len(bot.memory['streamSubs']) == 0:
            bot.say("You aren't subscribed to anything.")
            return
        s = None
        bot.reply(u'Sending you the list in pm.')
        for s in [a for a in bot.memory['streamSubs']
                  for n in bot.memory['streamSubs'][a] if n == nick]:
            bot.msg(nick, format_stream(s))
        if s:
            return
        bot.say("You aren't subscribed to anything.")
    elif arg == 'live' or arg == 'streaming':
        #Should be few enough streaming at any one time, just say in chat
        s = None
        for s in [a for a in bot.memory['streams'] if a.live]:
            bot.say(format_stream(s))
        if s:
            return
        bot.say("No one is streaming right now.")
    elif not arg:
        #Too many to say in chat, link to HTML list
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
        bot.say(u"I don't understand what you want me to list!")


def publish_lists(bot, trigger=None):
    def format_html(st):
        def wrap_link(link):
            return u'<a href = "%s">%s</a>' % (link, link)

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
        bot.debug(
            u'streams.py',
            u'IO error grabbing "list_main_dest_path" file contents. ' +
            u'File may not exist yet',
            u'warning'
        )

    try:
        with open(bot.memory['streamSet']['list_feat_dest_path'], 'r') as f:
            previous_feat_list = ''.join(f.readlines())
    except IOError:
        previous_feat_list = ''
        bot.debug(
            u'streams.py',
            u'IO error grabbing "list_feat_dest_path" file contents. ' +
            u'File may not exist yet',
            u'warning'
        )

    #Generate full list HTML
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
        with open(bot.memory['streamSet']['list_main_dest_path'], 'w') as f:
            f.write(contents)
    else:
        bot.debug(
            u'streams.py',
            u'No chage in full list html file, skipping.',
            u'verbose'
        )
    #Generate featured list HTML
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
        with open(bot.memory['streamSet']['list_feat_dest_path'], 'w') as f:
            f.write(contents)
    else:
        bot.debug(
            u'streams.py',
            u'No chage in featured list html file, skipping.',
            u'verbose'
        )
    return


@commands('services')
def services(bot, trigger):
    '''Propert input includes a URL by itself (e.g. http://justin.tv/tdreyer1)
 or a channel name / service name pair (e.g. tdreyer1 justin.tv). Accepted
 service names are justin.tv, livestream.com, twitch.tv, ustream.tv, and
 youtube.com'''
    bot.say(__doc__.strip())
    return


def remove_stream(bot, user):
    assert isinstance(user, basestring) or type(user) is tuple

    try:
        u, s = parse_service(user)
    except TypeError:
        bot.say('Bad url or channel/service pair. See !help services.')
        return
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    with bot.memory['streamLock']:
        for i in [a for a in bot.memory['streams']
                  if a.name == u and a.service == s]:
            try:
                cur.execute('''DELETE FROM feat_streams
                               WHERE channel = %s
                               AND service = %s''' % (_SUB * 2), (u, s))
                cur.execute('''DELETE FROM streams
                               WHERE channel = %s
                               AND service = %s''' % (_SUB * 2), (u, s))
                cur.execute('''DELETE FROM sub_streams
                               WHERE channel = %s
                               and service = %s''' % (_SUB * 2), (u, s))
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
            bot.say(u'Stream removed.')
            return
        else:
            bot.say(u"I don't have that stream.")


@commands('update', 'reload', 'refresh')
def update_streams(bot, trigger):
    with bot.memory['streamLock']:
        bot.reply(u'updating streams')
        for i in bot.memory['streams']:
            i.update()
            time.sleep(0.25)
        bot.reply(u'Streams updated')


def feature(bot, switch, channel, quiet=False):
    assert isinstance(channel, basestring) or type(channel) is tuple
    try:
        u, s = parse_service(channel)
    except TypeError:
        msg = u'Bad url or channel/service pair. See !help services.'
        if not quiet:
            bot.say(msg)
        else:
            bot.debug('streams:load_from_db', msg, 'warning')
        return
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    with bot.memory['streamLock']:
        if switch == 'feature':
            for i in [a for a in bot.memory['streams']
                      if a.name == u and a.service == s]:
                if i in bot.memory['feat_streams']:
                    msg = u"That's already featured!"
                    if not quiet:
                        bot.say(msg)
                    else:
                        bot.debug('streams:load_from_db', msg, 'warning')
                    return
                else:
                    try:
                        cur.execute('''SELECT COUNT(*) FROM feat_streams
                                       WHERE channel = %s
                                       AND service = %s''' % (_SUB * 2),
                                    (u, s))
                        if cur.fetchone()[0] == 0:
                            cur.execute('''INSERT INTO feat_streams
                                           (channel, service)
                                           VALUES (%s, %s)''' % (_SUB * 2),
                                        (u, s))
                            dbcon.commit()
                    finally:
                        cur.close()
                        dbcon.close()
                    bot.memory['feat_streams'].append(i)
                    msg = u'Stream featured.'
                    if not quiet:
                        bot.say(msg)
                    else:
                        bot.debug('streams:load_from_db', msg, 'warning')
                    return
            msg = u"Not a channel or that channel hasn't been added yet!"
            if not quiet:
                bot.say(msg)
            else:
                bot.debug('streams:load_from_db', msg, 'warning')
            return
        elif switch == 'unfeature':
            for i in [a for a in bot.memory['feat_streams']
                      if a.name == u and a.service == s]:
                try:
                    cur.execute('''DELETE FROM feat_streams
                                   WHERE channel = %s
                                   AND service = %s''' % (_SUB * 2), (u, s))
                    dbcon.commit()
                finally:
                    cur.close()
                    dbcon.close()
                bot.memory['feat_streams'].remove(i)
                msg = u'Stream unfeatured.'
                if not quiet:
                    bot.say(msg)
                else:
                    bot.debug('streams:load_from_db', msg, 'warning')
                return
            msg = u"Not a channel or that channel hasn't been added yet!"
            if not quiet:
                bot.say(msg)
            else:
                bot.debug('streams:load_from_db', msg, 'warning')
            return
        else:
            msg = u"Oh shit, I don't know what just happened."
            if not quiet:
                bot.reply(msg)
            else:
                bot.debug('streams:load_from_db', msg, 'warning')


def subscribe(bot, switch, channel, nick, quiet=False):
    assert isinstance(channel, basestring) or type(channel) is tuple
    assert isinstance(switch, basestring)
    assert isinstance(nick, Nick)
    try:
        u, s = parse_service(channel)
    except TypeError:
        msg = u'Bad url or channel/service pair. See !help services.'
        if not quiet:
            bot.say(msg)
        else:
            bot.debug('streams:subscribe', msg, 'warning')
        return
    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    with bot.memory['streamLock']:
        for i in [a for a in bot.memory['streams']
                  if a.name == u and a.service == s]:
            if switch == 'subscribe':
                if i not in bot.memory['streamSubs']:
                    bot.memory['streamSubs'][i] = []
                if nick not in bot.memory['streamSubs'][i]:
                    try:
                        cur.execute('''SELECT COUNT(*) FROM sub_streams
                                    WHERE channel = %s
                                    AND service = %s''' % (_SUB * 2),
                                    (u, s))
                        if cur.fetchone()[0] == 0:
                            cur.execute('''INSERT INTO sub_streams
                                        (channel, service, nick)
                                        VALUES (%s, %s, %s)''' % (_SUB * 3),
                                        (u, s, nick))
                            dbcon.commit()
                    finally:
                        cur.close()
                        dbcon.commit()
                    bot.memory['streamSubs'][i].append(nick)
                    msg = u'Subscription added.'
                    if not quiet:
                        bot.reply(msg)
                    else:
                        bot.debug('streams:subscribe', msg, 'warning')
                    return
                else:
                    msg = u"You're already subscribed to that channel!"
                    if not quiet:
                        bot.reply(msg)
                    else:
                        bot.debug('streams:subscribe', msg, 'warning')
            elif switch == 'unsubscribe':
                if i in bot.memory['streamSubs']:
                    if nick in bot.memory['streamSubs'][i]:
                        try:
                            cur.execute('''DELETE FROM sub_streams
                                           WHERE channel = %s
                                           AND service = %s
                                           AND nick = %s''' % (_SUB * 3),
                                        (u, s, nick))
                            dbcon.commit()
                        finally:
                            cur.close()
                            dbcon.close()
                        bot.memory['streamSubs'][i].remove(nick)
                        msg = u'Subscription removed.'
                        if not quiet:
                            bot.reply(msg)
                        else:
                            bot.debug('streams:subscribe', msg, 'warning')
                        return
                msg = u"You weren't subscribed to that or that doesn't exist."
                if not quiet:
                    bot.reply(msg)
                else:
                    bot.debug('streams:subscribe', msg, 'warning')
            else:
                msg = u"Oh shit, I don't know what just happened."
                if not quiet:
                    bot.reply(msg)
                else:
                    bot.debug('streams:subscribe', msg, 'warning')


@interval(19)
def announcer(bot):
    def whisper(nick, strm):
        bot.msg(nick, '%s has started streaming at %s' % (strm.name, strm.url))

    def announce(chan, strm):
        bot.msg(
            chan,
            'Hey everyone, %s has started streaming at %s' % (strm.name,
                                                              strm.url))
    bot.debug(u'streams.py', u'Announcer waking up', u'verbose')
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
            for n in bot.channels:
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
    bot.debug(u'streams.py', u'Announcer sleeping', u'verbose')


# Justin.tv caches for at least 60 seconds. Updating faster is pointless.
@interval(211)
def jtv_updater(bot):
    bot.debug(u'streams.py', u'Starting justin.tv updater.', u'verbose')
    now = time.time()
    for s in [i for i in bot.memory['streams'] if i.service == 'justin.tv']:
        s.update()
        time.sleep(0.25)
    bot.debug(u'streams.py',
              u'jtv updater complete in %s seconds.' % (time.time() - now),
              u'verbose')


# Livestream limits access to the following limits
#    10 requests per second
#    100 requests per minutes ( ~1 / 2sec )
#    1000 requests per hour ( ~1 / 3sec )
#    10000 requests per day ( ~1 / 9sec )
@interval(223)
def livestream_updater(bot):
    bot.debug(u'streams.py', u'Starting livestream.com updater.', u'verbose')
    now = time.time()
    for s in [i for i in bot.memory['streams'] if i.service == 'livestream.com']:
        s.update()
        time.sleep(0.25)
    bot.debug(
        u'streams.py',
        u'livestream.com updater complete in %s seconds.' % (time.time() - now),
        u'verbose'
    )


@interval(227)
def twitchtv_updater(bot):
    bot.debug(u'streams.py', u'Starting twitch.tv updater.', u'verbose')
    now = time.time()
    for s in [i for i in bot.memory['streams'] if i.service == 'twitch.tv']:
        s.update()
        time.sleep(0.25)
    bot.debug(
        u'streams.py',
        u'twitch.tv updater complete in %s seconds.' % (time.time() - now),
        u'verbose'
    )


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
    bot.say((u'There are %s from livestream.com, %s from justin.tv, ' +
             u'%s from twitch.tv, %s from youtube.com, and %s ' +
             u'from ustream.tv.') % (
            len([i for i in bot.memory['streams']
                if i.service == 'livestream.com']),
            len([i for i in bot.memory['streams']
                if i.service == 'justin.tv']),
            len([i for i in bot.memory['streams']
                if i.service == 'twitch.tv']),
            len([i for i in bot.memory['streams']
                if i.service == 'youtube.com']),
            len([i for i in bot.memory['streams']
                if i.service == 'ustream.tv'])
            ))
    bot.say(u'There are %s individual subscriptions.' %
            len(bot.memory['streamSubs']))


@commands('db_maint')
def update_database_tables(bot, trigger):
    if not trigger.admin:
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
    print __doc__.strip()
