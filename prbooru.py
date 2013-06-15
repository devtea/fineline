"""
prbooru.py - A simple Willie module to parse tags and return results from the
Pony Reference Booru
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from HTMLParser import HTMLParseError
from random import choice
import re

from bs4 import BeautifulSoup, SoupStrainer

import willie.web as web

base_url = u'http://ponyreference.booru.org/'

def parse_tags(tags):
    '''Takes a string, returns a list'''
    if tags:
        tag_list = tags.split(',')
        parsed = []
        for tag in tag_list:
            parsed.append(re.sub(' ', '_', tag.strip()))
        return parsed # like ['something', 'with_spaces']
    else:
        return None

def prbooru_search(willie, tags=None, rand=True):
    def get_image_from_page(url):
        page = ''
        try:
            page = web.get(url)
        except TimoutError:
            willie.debug('prbooru.py', 'Site timed out.', 'warning')
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
        except TimoutError:
            willie.debug('prbooru.py', 'TIMEOUT', 'verbose')
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
            soupy_links = soupy.find_all('a', id=re.compile(r'p\d{1,6}'))
            links_list = []
            for i in soupy_links:
                #willie.debug('prbooru.py', i['href'], 'verbose')
                links_list.append(base_url + i['href'])
            next = ''
            next_tag = soupy.find('a', alt='next', text='>')
            if next_tag:
                next = base_url + str(next_tag['href'])
            willie.debug('prbooru.py', '"next" is ' + next, 'verbose')
            willie.debug('prbooru.py', 'returning %i' % len(links_list), 'verbose')
            return (links_list, next)
        else:
            return None  # Error so return none

    willie.debug('prbooru.py', tags, 'verbose')
    if tags:
        tag_blob = u'index.php?page=post&s=list&tags='
        tag_blob = u'%s%s' % (tag_blob, tags.pop(0))
        for tag in tags:
            tag_blob = u'%s+%s' % (tag_blob, tag)
        willie.debug('prbooru.py', base_url + tag_blob, 'verbose')
        next_page = base_url + tag_blob
        links = []
        while next_page:
            newlinks, next_page = get_pr_list(next_page)
            links = links + newlinks
            willie.debug('prbooru.py', 'links %i' % len(links), 'verbose')
        willie.debug('prbooru.py', 'got back %i links' % len(links), 'verbose')
        try:
            if rand:
                link = choice(links)
            else:
                link = links[0]
        except IndexError:
            return []  # No results so return empty
        willie.debug('prbooru.py', 'link is ' + link, 'verbose')
        pic = get_image_from_page(link)
        return pic
    else:
        willie.debug('prbooru.py', 'entered random section', 'verbose')
        tag_blob = u'index.php?page=post&s=random'
        return get_image_from_page(base_url+tag_blob)


def prbooru(willie, trigger):
    ''' Pulls images from the Pony Reference Booru at random or by tag'''
    willie.debug('prbooru.py', '-'*20, 'verbose')
    if not trigger.group(2):
        # TODO give help
        willie.debug('prbooru.py', 'No args, assuming random', 'verbose')
        willie.reply('Try `%s: help pr`' % willie.nick)
        return
    tags_list = parse_tags(trigger.group(2))
    willie.debug('prbooru.py', tags_list, 'verbose')
    if len(tags_list) == 1 and tags_list[0].upper() == 'RANDOM':
        willie.debug('prbooru.py', 'random', 'verbose')
        link = prbooru_search(willie) # Request a random image else:
    else:
        if len(tags_list) == 1:
            willie.reply("Okay, this might take a few seconds.")
        willie.debug('prbooru.py', 'tags', 'verbose')
        link = prbooru_search(willie, tags=tags_list) # Get image from tags
    if link:
        willie.reply(link)
    elif link is None:
        willie.reply("Sorry, the booru is having issues right now...")
    else:
        willie.reply("That doesn't seem to exist, maybe you should go tag " +
                "a few untagged images...")
prbooru.example = '`!pr random` or `!pr tag1, tag two, three`'
prbooru.commands = ['pr']
prbooru.rate = 30

