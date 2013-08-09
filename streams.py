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
    '''docstring'''
    name = 'dummy'

    def __init__(self, name, alias=None):
        super(stream, self).__init__()
        self.name = name
        self.alias = alias
        self.live = False

    def is_live(self):
        '''Returns a boolean value for the live status of the stream.'''
        return self.live

    def update(self):
        # Dummy function to be extended by children. Use to hit the appropriate
        # streaming site and update object variables.
        return


class livestream(stream):
   # http://www.livestream.com/userguide/?title=Guide_API
    def __init__(self):
        super(livestream, self).__init__()
    pass


class newlivestream(stream):
    # http://www.livestream.com/userguide/?title=Channel_API_2.0
    pass


class justintv(stream):
    # http://www.justin.tv/p/api
    base_url = 'http://api.justin.tv/api/'
    header_info = ''

    def __init__(self, name, alias=None):
        super(justintv, self).__init__(name, alias)
        self.name = name
        self.update()

    def update(self):
        # Update stream info
        try:
            self.results = web.get(u'%sstream/list.json?channel=%s' % (
                self.base_url, self.name))
        except timeout:
            raise
        try:
            self.form_j = json.loads(self.results)
        except ValueError:
            print "Bad Json loaded from justin.tv"
            #print self.results
            raise
        except IndexError:
            raise
        except TypeError:
            raise
        if self.form_j:
            # We got results, so grab all info from here
            if not self.live:
                self.last_update = datetime.now()
                self.live = True
            print 'got json'
            print json.dumps(self.form_j, indent=4)
            try:
                raise ValueError(self.form_j['error'])
            except KeyError:
                # the object has no key 'error'
                pass
            except TypeError:
                # The object is probably valid, dict inside list
                pass
            # Load data
            self.id = self.form_j[0]['id']
            self.title = self.form_j[0]['title']
            #self.description = self.form_ji['channel']['description']
            #self.about = self.form_j['about']
            self.status = self.form_j[0]['channel']['status']
            self.category = self.form_j[0]['channel']['category']
            self.category_title = self.form_j[0]['channel']['category_title']
            self.subcategory = self.form_j[0]['channel']['subcategory']
            self.subcategory_title = self.form_j[0]['channel'][
                'subcategory_title']
            self.tags = self.form_j[0]['channel']['tags']
            self.mature = self.form_j[0]['channel']['mature']
            self.channel_url = self.form_j[0]['channel']['channel_url']
            print ''
            print 'id: %s' % self.id
            print 'title: %s' % self.title
            #print 'description: %s' % self.description
            #print 'about: %s' % self.about
            print 'status: %s' % self.status
            print 'category: %s' % self.category
            print 'category_title: %s' % self.category_title
            print 'subcategory: %s' % self.subcategory
            print 'subcategory_title: %s' % self.subcategory_title
            print 'tags: %s' % self.tags
            print 'mature: %s' % self.mature
            print 'url: %s' % self.channel_url
            print 'live: %s' % self.live
        else:
            # Update channel info only, no stream
            try:
                self.results = web.get(u'%schannel/show/%s.json' % (
                    self.base_url, self.name))
            except timeout:
                raise
            try:
                self.form_j = json.loads(self.results)
            except ValueError:
                print "Bad Json loaded from justin.tv"
                #print self.results
                raise
            except IndexError:
                raise
            except TypeError:
                raise
            if self.live:
                self.live = False
                self.last_update = datetime.now()
            print 'got json'
            print json.dumps(self.form_j, indent=4)
            try:
                raise ValueError(self.form_j['error'])
            except KeyError:
                pass
            # Load data
            self.id = self.form_j['id']
            self.title = self.form_j['title']
            self.description = self.form_j['description']
            self.about = self.form_j['about']
            self.status = self.form_j['status']
            self.category = self.form_j['category']
            self.category_title = self.form_j['category_title']
            self.subcategory = self.form_j['subcategory']
            self.subcategory_title = self.form_j['subcategory_title']
            self.tags = self.form_j['tags']
            self.mature = self.form_j['mature']
            self.channel_url = self.form_j['channel_url']
            print ''
            print 'id: %s' % self.id
            print 'title: %s' % self.title
            print 'description: %s' % self.description
            print 'about: %s' % self.about
            print 'status: %s' % self.status
            print 'category: %s' % self.category
            print 'category_title: %s' % self.category_title
            print 'subcategory: %s' % self.subcategory
            print 'subcategory_title: %s' % self.subcategory_title
            print 'tags: %s' % self.tags
            print 'mature: %s' % self.mature
            print 'url: %s' % self.channel_url
            print 'live: %s' % self.live


class twitchtv(justintv):
    # https://github.com/justintv/twitch-api
    pass


def setup(bot):
    # TODO remove these erasures when you load from database
    bot.memory['streams'] = []
    bot.memory['feat_streams'] = []

    # TODO Run through database and instantiate all stored streams
    if 'streams' not in bot.memory:
        bot.memory['streams'] = []


@commands('test')
def sceencasting(bot, trigger):
    #bob = justintv('http://justin.tv/tdreyer1')
    #print bob.name
    if len(trigger.args[1].split()) == 2:  # E.G. "!ls url"
        arg1 = trigger.args[1].split()[1].lower()
        # TODO Parse to see if URL or bad imput. Parse URL like 'add url'

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
            # TODO
            return
        elif arg1 == 'feature' or arg1 == 'unfeature':
            feature(bot, arg1, arg2)
            return
        elif arg1 == 'info' or arg1 == 'list':
            # TODO
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
            # TODO
            return
        elif arg1 == 'feature' or arg1 == 'unfeature':
            feature(bot, arg1, (arg2, arg3))
            return
        elif arg1 == 'info' or arg1 == 'list':
            # TODO
            list_streams(bot, arg2)
            return
    # TODO Print help, we either got nothing, or too much
    bot.reply("I don't understand that, try '!help livestream' for info.")


def parse_service(service):
    '''Takes a string or tuple (chan, service) and returns (chan, service)'''
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

    if s == 'livestream':
        # TODO test to see if it already exists
        # TODO Add to list
        return
    elif s == 'new.livestream':
        # TODO test to see if it already exists
        # TODO Add to list
        return
    elif s == 'justin.tv':
        for i in bot.memory['streams']:
            if i.name.lower() == u and isinstance(i, justintv):
                bot.reply(u'I already have that one.')
                return
        try:
            bot.memory['streams'].append(justintv(u))
        except ValueError as detail:
            bot.debug(u'streams.py',
                      u'Error adding jtv user: %s' % detail,
                      u'warning')
            bot.reply(u"Sorry, I couldn't find that channel.")
        else:
            bot.reply(u'Stream added.')
        return
    elif s == 'twitch.tv':
        # TODO test to see if it already exists
        # TODO Add to list
        return
    else:
        bot.say("Bad Input: this shouldn't ever happen...")
        # TODO say help message


def list_streams(bot, arg=None):
    if arg == 'featured':
        if len(bot.memory['feat_streams']) == 0:
            bot.say("I've got nothing.")
            return
        for i in bot.memory['feat_streams']:
            if isinstance(i, justintv):
                source = 'justin.tv'
            elif isinstance(i, livestream):
                source = 'livestream.com'
            elif isinstance(i, newlivestream):
                source = 'new.livestream.com'
            elif isinstance(i, twitchtv):
                source = 'twitch.tv'
            else:
                source = 'NONE?WTF'
            live = ''
            if i.is_live():
                # TODO Add color
                live = '[LIVE] '
            # TODO Add URL
            bot.say('%s%s on %s [ %s ]' % (
                live, i.name, source, i.channel_url))
        return
    elif arg == 'subscribed' or arg == 'subscriptions':
        # TODO
        return
    else:
        if len(bot.memory['streams']) == 0:
            bot.say("I've got nothing.")
            return
        for i in bot.memory['streams']:
            if isinstance(i, justintv):
                source = 'justin.tv'
            elif isinstance(i, livestream):
                source = 'livestream.com'
            elif isinstance(i, newlivestream):
                source = 'new.livestream.com'
            elif isinstance(i, twitchtv):
                source = 'twitch.tv'
            else:
                source = 'NONE?WTF'
            live = ''
            if i.is_live():
                # TODO Add color
                live = '[LIVE] '
            # TODO Add URL
            bot.say('%s%s on %s [ %s ]' % (
                live, i.name, source, i.channel_url))


def remove_stream(bot, user):
    assert type(user) is str or type(user) is unicode or type(user) is tuple
    try:
        u, s = parse_service(user)
    except TypeError:
        # TODO say help message
        bot.say('Bad Input')
        return
    if s == 'livestream':
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


if __name__ == "__main__":
    print __doc__.strip()
