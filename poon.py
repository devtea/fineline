# coding=utf-8
"""
poon.py - A simple Willie module to return links to derpy faces
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

Requires the following in the config:
[imgur]
client_id = ______
client_secret = _____
"""
from __future__ import print_function

import json, urllib2, random

from willie.module import commands

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

def setup(bot):
    bot.memory["imgur_client"] = bot.config.imgur.client_id
    update_poon(bot)

imgur_api_url = 'https://api.imgur.com/3/'
poon_album = 'YZmbK'

def imgur_anonymous_request(client_id, endpoint):
    req = urllib2.Request(imgur_api_url + endpoint)
    req.add_header('authorization', 'client-id ' + client_id)
    res = urllib2.urlopen(req)
    data = json.loads(res.read().decode('utf-8'))
    return data

def imgur_album_data(client_id, album_id):
    endpoint = 'album/' + album_id
    return imgur_anonymous_request(client_id, endpoint)

def update_poon(bot):
    bot.memory['poon_images'] = []
    data = imgur_album_data(bot.memory['imgur_client'], poon_album)
    for image in data['data']['images']:
        bot.memory['poon_images'].append(unicode(image['link']))

@commands(u'poon')
def poon(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    # if we don't have any images then do nothing
    if not bot.memory['poon_images'] or len(bot.memory['poon_images']) == 0:
        return

    url = random.choice(bot.memory['poon_images'])
    bot.say(url)


if __name__ == "__main__":
    print(__doc__.strip())
