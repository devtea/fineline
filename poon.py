# coding=utf-8
"""
poon.py - A simple Willie module to return links to derpy faces
Copyright 2013, Tim Dreyer, Porter Smith
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import json
import urllib2
import random
import traceback

from willie.module import commands, interval

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

_imgur_api_url = 'https://api.imgur.com/3/'
_poon_album = 'YZmbK'


def setup(bot):
    """
    | [imgur] | example | purpose |
    | client_id | k1j3k1lk388 | client_id from a registered imgur appliction |
    | client_secret | skj1831k3j1j31lk31k31j3lk3424514k | client_secret from a registered imgur application |
    """
    bot.memory["imgur_client_id"] = bot.config.imgur.client_id
    update_poon(bot)


def imgur_anonymous_request(bot, client_id, endpoint):
    try:
        req = urllib2.Request(_imgur_api_url + endpoint)
        req.add_header('authorization', 'client-id ' + client_id)
        res = urllib2.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        return data
    except:
        bot.debug(__file__, log.format('Unhandled exception in imgur_anonymous_request.'), 'warning')
        bot.debug(__file__, traceback.format_exc(), 'warning')


def imgur_album_data(bot, client_id, album_id):
    endpoint = 'album/' + album_id
    return imgur_anonymous_request(bot, client_id, endpoint)


@interval(2500)
def update_poon(bot):
    data = imgur_album_data(bot, bot.memory['imgur_client_id'], _poon_album)
    bot.memory['poon_images'] = [unicode(i['link']) for i in data['data']['images']]


@commands(u'poon')
def poon(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    # If we don't have any images then do nothing
    if bot.memory['poon_images']:
        bot.say(random.choice(bot.memory['poon_images']))


if __name__ == "__main__":
    print(__doc__.strip())
