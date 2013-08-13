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
import sys
from socket import timeout

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


_re_jtv = re.compile('(?<=justin\.tv/)[^/(){}[\]]+')
_re_ttv = re.compile('(?<=twitch\.tv/)[^/(){}[\]]+')
_re_nls = re.compile('(?<=new\.livestream\.com/)[^/(){}[\]]+')
_re_ls = re.compile('(?<=livestream\.com/)[^/(){}[\]]+')
_re_us = re.compile('(?<=ustream\.tv/)[^/(){}[\]]+')
_re_yt = re.compile('(?<=youtube\.com/)[^/(){}[\]]+')
#_url_finder = re.compile(r'(?u)(%s?(?:http|https)(?:://\S+))')
_services = ['justin.tv', 'twitch.tv', 'new.livestream', 'livestream']
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
        self._name = name
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
            #print 'got json'
            #print json.dumps(self._form_j, indent=4)
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
            # No results means stream's not live
            if self._live:
                self._live = False
                self._last_update = time.time()
        self._url = self._settings['channel_url']
        # NSFW flag is one of ['true', 'false', None]
        if self._settings['mature'] == 'true':
            self._nsfw = True
        else:
            self._nsfw = False


class livestream(stream):
    # http://www.livestream.com/userguide/index.php?title=Channel_API_2.0
    _base_url = '.api.channel.livestream.com/2.0/'
    _service = 'livestream'
    _last_update = time.time()
    #_header_info = ''

    def __init__(self, name, alias=None):
        super(livestream, self).__init__(name, alias)
        self._name = name
        self._safename = re.sub('_', '-', name)
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
        #print 'got json'
        #print json.dumps(self._form_j, indent=4)
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
        #print 'got json'
        #print json.dumps(self._form_j, indent=4)
        for s in self._form_j['channel']:
            self._settings[s] = self._form_j['channel'][s]
        if bool(self._live) ^ bool(self._settings['isLive']):
            self._live = self._settings['isLive']
            self._last_update = time.time()


class newlivestream(stream):
    # http://www.livestream.com/userguide/?title=Channel_API_2.0
    pass


class ustream(stream):
    pass


class youtube(stream):
    pass


class twitchtv(justintv):
    # https://github.com/justintv/twitch-api

    pass


class StreamFactory(object):
    def newStream(self, channel, service):
        # TODO catch exceptions from object instantiations
        if service == 'justin.tv':
            return justintv(channel)
        elif service == 'twitch.tv':
            return twitchtv(channel)
        elif service == 'new.livesteam':
            return newlivestream(channel)
        elif service == 'livestream':
            try:
                return livestream(channel)
            except ValueError as txt:
                if txt == 'ValueError: 400 Bad Request':
                    raise ValueError('400 Bad Request')
                elif txt == 'ValueError: 404 Not Found':
                    raise ValueError('404 Not Found')
                elif txt == 'ValueError: 500 Internal Server Error':
                    raise ValueError('500 Internal Server Error')
                else:
                    raise
        elif service == 'youtube':
            return youtube(channel)
        elif service == 'ustream.tv':
            return ustream(channel)
        else:
            return None


def setup(bot):
    bot.debug(
        u'streams.py',
        u'Starting stream setup, this may take a bit.',
        'always'
    )
    # TODO consider making these unique sets
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
                           (channel text, service text)''')
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
    with bot.memory['streamLock']:
        bot.memory['streams'] = []
        bot.memory['feat_streams'] = []
        dbcon = bot.db.connect()  # sqlite3 connection
        cur = dbcon.cursor()
        try:
            cur.execute('SELECT channel, service FROM streams')
            stream_rows = cur.fetchall()
            cur.execute('SELECT channel, service FROM feat_streams')
            feat_rows = cur.fetchall()
            cur.execute('SELECT channel, service, nick FROM sub_streams')
            sub_rows = cur.fetchall()
        finally:
            cur.close()
            dbcon.close()
        for c, s in stream_rows:
            time.sleep(2)
            bot.memory['streams'].append(bot.memory['streamFac'].newStream(c,
                                                                           s))
    for c, s in feat_rows:
        feature(bot, 'feature', (c, s), quiet=True)
    for c, s, n in sub_rows:
        subscribe(bot, 'subscribe', (c, s), Nick(n), quiet=True)
    bot.debug(u'streams.py:reload', u'Done.', 'verbose')


@commands('live')
def sceencasting(bot, trigger):
    '''Manage various livestreams from multiple services.
 Usage: !live [add/del/[un]subscribe/[un]feature/list] [options] |
 ADD URL-adds a stream to the library |
 DEL URL-removes a stream from the library |
 LIST [<blank>/featured/subscriptions]-lists all/featured/subcribed streams |
 [UN]SUBSCRIBE URL-[un]set private messages on going live |
 [UN]FEATURE URL-[un]set public announcement on going live'''
    if len(trigger.args[1].split()) == 2:  # E.G. "!stream url"
        arg1 = trigger.args[1].split()[1].lower()
        if arg1 == 'list':
            list_streams(bot, nick=Nick(trigger.nick))
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
        elif _re_nls.search(service):
            return (_re_nls.findall(service)[0], 'new.livestream')
        elif _re_ls.search(service):
            return (_re_ls.findall(service)[0], 'livestream')
        elif _re_yt.search(service):
            return (_re_ls.findall(service)[0], 'youtube')
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
                if txt == 'ValueError: 400 Bad Request':
                    bot.reply(u'Oops, I did something bad, so that did not ' +
                              u'work.')
                    bot.say('!tell tdreyer1 FIX IT FIX IT FIX IT FIX IT!')
                    return
                elif txt == 'ValueError: 404 Not Found':
                    bot.reply(u'Channel not found.')
                    return
                elif txt == 'ValueError: 500 Internal Server Error':
                    bot.reply(u'Service returned internal server error, try' +
                              u' again later.')
                    return
                else:
                    bot.reply(u'There was an unknown error, check your ' +
                              u'spelling and try again later')
                    print txt
                    return
            try:
                cur.execute('''SELECT COUNT(*) FROM streams
                               WHERE channel = %s
                               AND service = %s''' % (_SUB * 2), (u, s))
                if cur.fetchone()[0] == 0:
                    print 'ADD: count was != 0'
                    cur.execute('''INSERT INTO streams (channel, service)
                                   VALUES (%s, %s)''' % (_SUB * 2), (u, s))
                    dbcon.commit()
            finally:
                cur.close()
                dbcon.close()
        bot.say('added stream')


def list_streams(bot, arg=None, nick=None):
    def format_stream(st):
        nsfw = ''
        if st.nsfw:
            nsfw = '[%s] ' % colors.colorize('NSFW', ['red'], ['b'])
        live = ''
        if st.live:
            live = '[%s] ' % colors.colorize('LIVE', ['green'], ['b'])
        return '%s%s%s [ %s ]' % (nsfw, live, st, colors.colorize(st.url,
                                                                  ['blue']))
    # TODO add option to list only live streams
    if arg == 'featured':
        if len(bot.memory['feat_streams']) == 0:
            bot.say("I've got nothing.")
            return
        bot.reply(u'Sending you the list in pm.')
        for i in bot.memory['feat_streams']:
            bot.msg(nick, format_stream(i))
        return
    elif arg == 'subscribed' or arg == 'subscriptions':
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
    elif not arg:
        if len(bot.memory['streams']) == 0:
            bot.say("I've got nothing.")
            return
        bot.reply(u'Sending you the list in pm.')
        for i in bot.memory['streams']:
            bot.msg(nick, format_stream(i))
    else:
        bot.say(u"I don't understand what you want me to list!")


@commands('services')
def services(bot, trigger):
    '''Propert input includes a URL by itself (e.g. http://justin.tv/tdreyer1)
 or a channel name / service name pair (e.g. tdreyer1 justin.tv). Accepted
 service names are justin.tv, livestream, twitch.tv, ustream.tv, and youtube'''
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
            time.sleep(10)
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


@interval(60)
def announcer(bot):
    def whisper(nick, strm):
        bot.msg(nick, '%s has started streaming at %s' % (strm.name, strm.url))

    def announce(chan, strm):
        bot.msg(
            chan,
            'Hey everyone, %s has started streaming at %s' % (strm.name,
                                                              strm.url))
    print 'Announcer waking up'
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
    print 'Announcer sleeping'''


# Justin.tv caches for at least 60 seconds. Updating faster is pointless.
@interval(5 * 60)
def jtv_updater(bot):
    print 'starting jtv updater'
    now = time.time()
    for s in [i for i in bot.memory['streams'] if i.service == 'justin.tv']:
        s.update()
        time.sleep(1)
    print 'jtv updater complete in %s seconds.' % (time.time() - now)


# Livestream limits access to the following limits
#    10 requests per second
#    100 requests per minutes ( ~1 / 2sec )
#    1000 requests per hour ( ~1 / 3sec )
#    10000 requests per day ( ~1 / 9sec )
@interval(5 * 60)
def livestream_updater(bot):
    print 'starting livestream updater'
    now = time.time()
    for s in [i for i in bot.memory['streams'] if i.service == 'livestream']:
        s.update()
        time.sleep(1)
    print 'livestream updater complete in %s seconds.' % (time.time() - now)


def info():
    # TODO
    return


def url_watcher():
    # TODO Write function that watches for stream URLs in chat, and post info
    # about them. Don't forget to exclude these from the regular URL watcher
    return


def stats():
    # TODO Need a function that will report stats like number of streams,
    # number of featured, number of subs, steams by service
    return


if __name__ == "__main__":
    print __doc__.strip()
