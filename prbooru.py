"""
prbooru.py - A simple willie module to parse tags and return results from the
Pony Reference Booru
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

from HTMLParser import HTMLParseError
from random import choice
from socket import timeout

import bisect
import os.path
import re
import random

from bs4 import BeautifulSoup, SoupStrainer

import willie.web as web
from willie.module import commands, example

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        print("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()

base_urls = [(u'http://ponyresource.booru.org/', 1557), (u'http://ponyreference.booru.org/', 817)]


def parse_tags(tags):
    '''Takes a string, returns a list'''
    if tags:
        tag_list = tags.split(u',')
        parsed = []
        for tag in tag_list:
            parsed.append(re.sub(u' ', u'_', tag.strip()))
        return parsed  # like ['something', 'with_spaces']
    else:
        return None


def prbooru_search(bot, booru, tags=None, rand=True):
    def get_image_from_page(url):
        page = ''
        try:
            page = web.get(url)
        except timeout:
            bot.debug(__file__, log.format(u'Site timed out.'), u'warning')
            return None
        if page:
            try:
                # Tried lxml but no difference for this application
                img_tags = SoupStrainer(u"img")
                soupy = BeautifulSoup(page, parse_only=img_tags)
            except HTMLParseError:
                return None
            except:
                raise
            image = soupy.find(u'img', id=u'image')[u'src']
            return image
        else:
            return None  # Error, so return None

    def get_pr_list(url):
        page = ''
        try:
            page = web.get(url)
        except timeout:
            bot.debug(__file__, log.format(u'TIMEOUT'), u'verbose')
            return None
        if page:
            try:
                # Tried lxml but no real difference for this application
                a_tags = SoupStrainer(u"a")
                soupy = BeautifulSoup(page, parse_only=a_tags)
            except HTMLParseError:
                return None
            except:
                raise
            soupy_links = soupy.find_all(u'a', id=re.compile(ur'p\d{1,6}'))
            links_list = []
            for i in soupy_links:
                # bot.debug(__file__, log.format(i['href']), 'verbose')
                links_list.append(booru + i[u'href'])
            next = ''
            next_tag = soupy.find(u'a', alt=u'next', text=u'>')
            if next_tag:
                next = booru + str(next_tag['href'])
            bot.debug(__file__, log.format(u'"next" is ', next), u'verbose')
            bot.debug(__file__, log.format(u'returning %i' % len(links_list)), u'verbose')
            return (links_list, next)
        else:
            return None  # Error so return none

    bot.debug(__file__, log.format(tags), u'verbose')
    if tags:
        tag_blob = u'index.php?page=post&s=list&tags='
        tag_blob = u'%s%s' % (tag_blob, tags.pop(0))
        for tag in tags:
            tag_blob = u'%s+%s' % (tag_blob, tag)
        bot.debug(__file__, log.format(booru, tag_blob), u'verbose')
        next_page = booru + tag_blob
        links = []
        while next_page:
            newlinks, next_page = get_pr_list(next_page)
            links = links + newlinks
            bot.debug(__file__, log.format(u'links %i' % len(links)), u'verbose')
        bot.debug(__file__,
                  log.format(u'got back %i links' % len(links)),
                  u'verbose'
                  )
        try:
            if rand:
                link = choice(links)
            else:
                link = links[0]
        except IndexError:
            return []  # No results so return empty
        bot.debug(__file__, log.format(u'link is %s' % link), u'verbose')
        pic = get_image_from_page(link)
        return pic
    else:
        bot.debug(__file__, log.format(u'entered random section'), u'verbose')
        tag_blob = u'index.php?page=post&s=random'
        return get_image_from_page(booru + tag_blob)


def weighted_choice(weighted):
    """Returns a random index from a list of tuples that contain
    (something, weight) where weight is the weighted probablity that
    that item should be chosen. Higher weights are chosen more often"""
    sum = 0
    sum_steps = []
    for item in weighted:
        sum = sum + int(item[1])
        sum_steps.append(sum)
    return bisect.bisect_right(sum_steps, random.uniform(0, sum))


@commands(u'pr')
@example(u'`!pr random` or `!pr tag1, tag two, three`')
def prbooru(bot, trigger):
    '''Pulls images from one of the reference boorus at random or by specified tag.'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    booru = base_urls[weighted_choice(base_urls)][0]

    bot.debug(__file__, log.format(u'-' * 20), u'verbose')
    if not trigger.group(2):
        # TODO give help
        bot.debug(__file__, log.format(u'No args, assuming random'), u'verbose')
        bot.reply(u'Try `%s: help pr`' % bot.nick)
        return
    tags_list = parse_tags(trigger.group(2))
    bot.debug(__file__, log.format(tags_list), u'verbose')
    if len(tags_list) == 1 and tags_list[0].upper() == u'RANDOM':
        bot.debug(__file__, log.format(u'random'), u'verbose')
        link = prbooru_search(bot, booru)  # Request a random image else:
    else:
        bot.debug(__file__, log.format(u'tags'), u'verbose')
        link = prbooru_search(bot, booru, tags=tags_list)  # Get image from tags
    if link:
        bot.reply(link)
    elif link is None:
        bot.reply(u"Sorry, the booru is having issues right now...")
    else:
        bot.reply(u"That doesn't seem to exist, maybe you should go tag " +
                  u"a few untagged images..."
                  )


if __name__ == "__main__":
    print(__doc__.strip())
