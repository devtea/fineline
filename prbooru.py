"""
prbooru.py - A simple willie module to parse tags and return results from the
Pony Reference Booru
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from HTMLParser import HTMLParseError
from random import choice
from socket import timeout

import bisect
import re
import random

from bs4 import BeautifulSoup, SoupStrainer

from willie.logger import get_logger
from willie.module import commands, example
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

base_urls = [('http://ponyresource.booru.org/', 1557), ('http://ponyreference.booru.org/', 817)]


def parse_tags(tags):
    '''Takes a string, returns a list'''
    if tags:
        tag_list = tags.split(',')
        parsed = []
        for tag in tag_list:
            parsed.append(re.sub(' ', '_', tag.strip()))
        return parsed  # like ['something', 'with_spaces']
    else:
        return None


def prbooru_search(bot, booru, tags=None, rand=True):
    def get_image_from_page(url):
        page = ''
        try:
            page = web.get(url)
        except timeout:
            LOGGER.warning(log.format('Site timed out.'))
            return None
        if page:
            try:
                # Tried lxml but no difference for this application
                img_tags = SoupStrainer("img")
                soupy = BeautifulSoup(page, parse_only=img_tags)
            except HTMLParseError:
                return None
            except:
                raise
            image = soupy.find('img', id='image')['src']
            return image
        else:
            return None  # Error, so return None

    def get_pr_list(url):
        page = ''
        try:
            page = web.get(url)
        except timeout:
            LOGGER.warning(log.format('Site timed out.'))
            return None
        if page:
            try:
                # Tried lxml but no real difference for this application
                a_tags = SoupStrainer("a")
                soupy = BeautifulSoup(page, parse_only=a_tags)
            except HTMLParseError:
                return None
            except:
                raise
            soupy_links = soupy.find_all('a', id=re.compile(ur'p\d{1,6}'))
            links_list = []
            for i in soupy_links:
                # LOGGER.info(log.format(i['href']))
                links_list.append(booru + i['href'])
            next = ''
            next_tag = soupy.find('a', alt='next', text='>')
            if next_tag:
                next = booru + str(next_tag['href'])
            LOGGER.info(log.format('"next" is %s'), next)
            LOGGER.info(log.format('returning %i'), len(links_list))
            return (links_list, next)
        else:
            return None  # Error so return none

    LOGGER.info(log.format(tags))
    if tags:
        tag_blob = 'index.php?page=post&s=list&tags='
        tag_blob = '%s%s' % (tag_blob, tags.pop(0))
        for tag in tags:
            tag_blob = '%s+%s' % (tag_blob, tag)
        LOGGER.info(log.format(booru, tag_blob))
        next_page = booru + tag_blob
        links = []
        while next_page:
            newlinks, next_page = get_pr_list(next_page)
            links = links + newlinks
            LOGGER.info(log.format('links %i'), len(links))
        LOGGER.info(log.format('got back %i links'), len(links))
        try:
            if rand:
                link = choice(links)
            else:
                link = links[0]
        except IndexError:
            return []  # No results so return empty
        LOGGER.info(log.format('link is %s'), link)
        pic = get_image_from_page(link)
        return pic
    else:
        LOGGER.info(log.format('entered random section'))
        tag_blob = 'index.php?page=post&s=random'
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


@commands('pr')
@example('`!pr random` or `!pr tag1, tag two, three`')
def prbooru(bot, trigger):
    '''Pulls images from one of the reference boorus at random or by specified tag.'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    booru = base_urls[weighted_choice(base_urls)][0]

    LOGGER.info(log.format('-' * 20))
    if not trigger.group(2):
        # TODO give help
        LOGGER.info(log.format('No args, assuming random'))
        bot.reply('Try `%s: help pr`' % bot.nick)
        return
    tags_list = parse_tags(trigger.group(2))
    LOGGER.info(log.format(tags_list))
    if len(tags_list) == 1 and tags_list[0].upper() == 'RANDOM':
        LOGGER.info(log.format('random'))
        link = prbooru_search(bot, booru)  # Request a random image else:
    else:
        LOGGER.info(log.format('tags'))
        link = prbooru_search(bot, booru, tags=tags_list)  # Get image from tags
    if link:
        bot.reply(link)
    elif link is None:
        bot.reply("Sorry, the booru is having issues right now...")
    else:
        bot.reply("That doesn't seem to exist, maybe you should go tag " +
                  "a few untagged images..."
                  )


if __name__ == "__main__":
    print(__doc__.strip())
