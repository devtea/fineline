"""
streams.py - A simple willie module to track livestreams from popular services
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import json
import re
import time
from socket import timeout
from datetime import datetime

import willie.web as web
from willie.module import commands

_re_jtv = re.compile('(?<=justin\.tv/)[^/(){}[\]]+')
_re_ttv = re.compile('(?<=twitch\.tv/)[^/(){}[\]]+')
_re_nls = re.compile('(?<=new\.livestream\.com/)[^/(){}[\]]+')
_re_ls = re.compile('(?<=livestream\.com/)[^/(){}[\]]+')
#_url_finder = re.compile(r'(?u)(%s?(?:http|https)(?:://\S+))')
_services = ['justin.tv', 'twitch.tv', 'new.livestream', 'livestream']


class stream(object):
    '''General stream object. To be extended for each individual API.'''
    _url = None
    _settings = {}
    _live = False
    _nsfw = False
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
        return self.name()

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

    def update(self):
        # Dummy function to be extended by children. Use to hit the appropriate
        # streaming site and update object variables.
        return


class justintv(stream):
    # http://www.justin.tv/p/api
    _base_url = 'http://api.justin.tv/api/'
    _service = 'justin.tv'
    #_header_info = ''

    def __init__(self, name, alias=None):
        super(justintv, self).__init__(name, alias)
        self._name = name
        self.update()

    def update(self):
        # Update stream info
        try:
            # TODO move this url shit to a variable
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
                self._last_update = datetime.now()
                self._live = True
            print 'got json'
            print json.dumps(self._form_j, indent=4)
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
            # Update channel info only, no stream
            try:
                # TODO move this url shit to a variable
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
            if self._live:
                self._live = False
                self._last_update = datetime.now()
            print 'got json'
            print json.dumps(self._form_j, indent=4)
            try:
                raise ValueError(self._form_j['error'])
            except KeyError:
                pass
            for s in self._form_j:
                self._settings[s] = self._form_j[s]
        self._url = self._settings['channel_url']
        # NSFW flag is either True or None
        if self._settings['mature']:
            self._nsfw = True
        else:
            self._nsfw = False


class youtube(stream):
    pass


class ustream(stream):
    pass


class livestream(stream):
   # http://www.livestream.com/userguide/?title=Guide_API
    def __init__(self):
        super(livestream, self).__init__()
    pass


class newlivestream(stream):
    # http://www.livestream.com/userguide/?title=Channel_API_2.0
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
            return livestream(channel)
        else:
            return None


def setup(bot):
    # TODO remove these erasures when you load from database
    # TODO consider making these unique sets
    bot.memory['streams'] = []
    bot.memory['feat_streams'] = []
    bot.memory['streamFac'] = StreamFactory()

    # TODO Run through database and instantiate all stored streams
    if 'streams' not in bot.memory:
        bot.memory['streams'] = []
    if 'feat_streams' not in bot.memory:
        bot.memory['feat_streams'] = []
    if 'streamFac' not in bot.memory:
        bot.memory['streamFac'] = StreamFactory()


@commands('test')
def sceencasting(bot, trigger):
    if len(trigger.args[1].split()) == 2:  # E.G. "!ls url"
        arg1 = trigger.args[1].split()[1].lower()
        if arg1 == 'list':
            list_streams(bot)
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
            subscribe(bot, arg1, arg2)
            return
        elif arg1 == 'feature' or arg1 == 'unfeature':
            feature(bot, arg1, arg2)
            return
        elif arg1 == 'info' or arg1 == 'list':
            list_streams(bot, arg2)
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
            subscribe(bot, arg1, (arg2, arg3))
            return
        elif arg1 == 'feature' or arg1 == 'unfeature':
            feature(bot, arg1, (arg2, arg3))
            return
        elif arg1 == 'info' or arg1 == 'list':
            list_streams(bot, arg1, (arg2, arg3))
            return
    # TODO Print help, we either got nothing, or too much
    bot.reply("I don't understand that, try '!help livestream' for info.")


def parse_service(service):
    '''Takes a url string or tuple and returns (chan, service)'''
    assert type(service) is str or type(service) is unicode or \
        type(service) is tuple
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
        else:
            return None


def add_stream(bot, user):
    assert type(user) is str or type(user) is unicode or type(user) is tuple

    try:
        u, s = parse_service(user)
    except TypeError:
        bot.say('Bad Input')
        return
        # TODO say help message
    if [a for a in bot.memory['streams'] if a.name == u and a.service == s]:
        bot.reply(u'I already have that one.')
        return
    else:
        # TODO may need a try block here
        bot.memory['streams'].append(bot.memory['streamFac'].newStream(u, s))
        bot.say('added stream')


def list_streams(bot, arg=None):
    # TODO add logic to /msg when list is too long (>4?)
    if arg == 'featured':
        if len(bot.memory['feat_streams']) == 0:
            bot.say("I've got nothing.")
            return
        for i in bot.memory['feat_streams']:
            nsfw = ''
            if i.nsfw:
                # TODO Add color
                nsfw = '[NSFW] '
            live = ''
            if i.live:
                # TODO Add color
                live = '[LIVE] '
            bot.say('%s%s%s [ %s ]' % (nsfw, live, i, i.url))
        return
    elif arg == 'subscribed' or arg == 'subscriptions':
        # TODO
        return
    else:
        if len(bot.memory['streams']) == 0:
            bot.say("I've got nothing.")
            return
        for i in bot.memory['streams']:
            nsfw = ''
            if i.nsfw:
                # TODO Add color
                nsfw = '[NSFW] '
            live = ''
            if i.live:
                # TODO Add color
                live = '[LIVE] '
            # TODO Add URL
            bot.say('%s%s%s [ %s ]' % (nsfw, live, i, i.url))


def remove_stream(bot, user):
    assert type(user) is str or type(user) is unicode or type(user) is tuple
    try:
        u, s = parse_service(user)
    except TypeError:
        # TODO say help message
        bot.say('Bad Input')
        return
    if s == 'livestream':
        # TODO implement some kind of eq() to streamline this
        for i in bot.memory['streams']:
            if i.name.lower() == u.lower() and isinstance(i, livestream):
                bot.memory['streams'].remove(i)
                try:
                    bot.memory['feat_streams'].remove(i)
                except ValueError:
                    pass
                bot.say(u'Stream removed.')
                return
    elif s == 'new.livestream':
        for i in bot.memory['streams']:
            if i.name.lower() == u.lower() and isinstance(i, newlivestream):
                bot.memory['streams'].remove(i)
                try:
                    bot.memory['feat_streams'].remove(i)
                except ValueError:
                    pass
                bot.say(u'Stream removed.')
                return
    elif s == 'justin.tv':
        for i in bot.memory['streams']:
            if i.name.lower() == u.lower() and isinstance(i, justintv):
                bot.memory['streams'].remove(i)
                try:
                    bot.memory['feat_streams'].remove(i)
                except ValueError:
                    pass
                bot.say(u'Stream removed.')
                return
    else:
        for i in bot.memory['streams']:
            if i.name.lower() == u.lower() and isinstance(i, twitchtv):
                bot.memory['streams'].remove(i)
                try:
                    bot.memory['feat_streams'].remove(i)
                except ValueError:
                    pass
                bot.say(u'Stream removed.')
                return
    bot.say(u"I don't have that stream.")


@commands('update', 'reload', 'refresh')
def update_streams(bot, trigger):
    bot.reply(u'updating streams')
    for i in bot.memory['streams']:
        i.update()
        time.sleep(10)
    bot.reply(u'Streams updated')


def subscribe():
    # Allows users to soft subscribe to a stream and get whispers on live
    # status change
    return


def feature(bot, switch, channel):
    assert isinstance(channel, basestring) or type(channel) is tuple
    try:
        u, s = parse_service(channel)
    except TypeError:
        # TODO say help message
        bot.say('Bad Input')
        return
    if switch == 'feature':
        if s == 'livestream':
            for i in bot.memory['streams']:
                if i.name.lower() == u.lower() and isinstance(i, livestream):
                    if i in bot.memory['feat_streams']:
                        bot.say(u"That's already featured!")
                        return
                    else:
                        bot.memory['feat_streams'].append(i)
                        bot.say(u'Done!')
                        return
        elif s == 'new.livestream':
        # TODO implement some kind of eq() to streamline this
            for i in bot.memory['streams']:
                if i.name.lower() == u.lower() and \
                        isinstance(i, newlivestream):
                    if i in bot.memory['feat_streams']:
                        bot.say(u"That's already featured!")
                        return
                    else:
                        bot.memory['feat_streams'].append(i)
                        bot.say(u'Done!')
                        return
        elif s == 'justin.tv':
            for i in bot.memory['streams']:
                if i.name.lower() == u.lower() and isinstance(i, justintv):
                    if i in bot.memory['feat_streams']:
                        bot.say(u"That's already featured!")
                        return
                    else:
                        bot.memory['feat_streams'].append(i)
                        bot.say(u'Done!')
                        return
        else:
            for i in bot.memory['streams']:
                if i.name.lower() == u.lower() and isinstance(i, twitchtv):
                    if i in bot.memory['feat_streams']:
                        bot.say(u"That's already featured!")
                        return
                    else:
                        bot.memory['feat_streams'].append(i)
                        bot.say(u'Done!')
                        return
        bot.say(u"Not a channel or that channel hasn't been added yet!")
        return
    else:
        # TODO remove featured channel
        # TODO implement some kind of eq() to streamline this
        if s == 'livestream':
            for i in bot.memory['feat_streams']:
                if i.name.lower() == u.lower() and isinstance(i, livestream):
                    bot.memory['feat_streams'].remove(i)
                    bot.say(u'Done!')
                    return
        elif s == 'new.livestream':
            for i in bot.memory['feat_streams']:
                if i.name.lower() == u.lower() and \
                        isinstance(i, newlivestream):
                    bot.memory['feat_streams'].remove(i)
                    bot.say(u'Done!')
                    return
        elif s == 'justin.tv':
            for i in bot.memory['feat_streams']:
                if i.name.lower() == u.lower() and isinstance(i, justintv):
                    bot.memory['feat_streams'].remove(i)
                    bot.say(u'Done!')
                    return
        else:
            for i in bot.memory['feat_streams']:
                if i.name.lower() == u.lower() and isinstance(i, twitchtv):
                    bot.memory['feat_streams'].remove(i)
                    bot.say(u'Done!')
                    return
        # TODO
        bot.say('bad data or channel not featured')


def info():
    # TODO
    return


def url_watcher():
    # TODO Write function that watches for stream URLs in chat, and post info
    # about them. Don't forget to exclude these from the regular URL watcher
    return

if __name__ == "__main__":
    print __doc__.strip()
