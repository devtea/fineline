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
import re

from bs4 import BeautifulSoup, SoupStrainer

import willie.web as web
from willie.module import commands, example

base_url = u'http://ponyreference.booru.org/'


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


def prbooru_search(bot, tags=None, rand=True):
    def get_image_from_page(url):
        page = ''
        try:
            page = web.get(url)
        except timeout:
            bot.debug(u'prbooru.py', u'Site timed out.', u'warning')
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
            bot.debug(u'prbooru.py', u'TIMEOUT', u'verbose')
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
                #bot.debug('prbooru.py', i['href'], 'verbose')
                links_list.append(base_url + i[u'href'])
            next = ''
            next_tag = soupy.find(u'a', alt=u'next', text=u'>')
            if next_tag:
                next = base_url + str(next_tag['href'])
            bot.debug(u'prbooru.py', u'"next" is ' + next, u'verbose')
            bot.debug(u'prbooru.py',
                      u'returning %i' % len(links_list),
                      u'verbose'
                      )
            return (links_list, next)
        else:
            return None  # Error so return none

    bot.debug(u'prbooru.py', tags, u'verbose')
    if tags:
        tag_blob = u'index.php?page=post&s=list&tags='
        tag_blob = u'%s%s' % (tag_blob, tags.pop(0))
        for tag in tags:
            tag_blob = u'%s+%s' % (tag_blob, tag)
        bot.debug(u'prbooru.py', base_url + tag_blob, u'verbose')
        next_page = base_url + tag_blob
        links = []
        while next_page:
            newlinks, next_page = get_pr_list(next_page)
            links = links + newlinks
            bot.debug(u'prbooru.py', u'links %i' % len(links), u'verbose')
        bot.debug(u'prbooru.py',
                  u'got back %i links' % len(links),
                  u'verbose'
                  )
        try:
            if rand:
                link = choice(links)
            else:
                link = links[0]
        except IndexError:
            return []  # No results so return empty
        bot.debug(u'prbooru.py', u'link is %s' % link, u'verbose')
        pic = get_image_from_page(link)
        return pic
    else:
        bot.debug(u'prbooru.py', u'entered random section', u'verbose')
        tag_blob = u'index.php?page=post&s=random'
        return get_image_from_page(base_url + tag_blob)


@commands(u'pr')
@example(u'`!pr random` or `!pr tag1, tag two, three`')
def prbooru(bot, trigger):
    ''' Pulls images from the Pony Reference Booru at random or by tag'''
    bot.debug(u'prbooru.py', u'-' * 20, u'verbose')
    if not trigger.group(2):
        # TODO give help
        bot.debug(u'prbooru.py', u'No args, assuming random', u'verbose')
        bot.reply(u'Try `%s: help pr`' % bot.nick)
        return
    tags_list = parse_tags(trigger.group(2))
    bot.debug(u'prbooru.py', tags_list, u'verbose')
    if len(tags_list) == 1 and tags_list[0].upper() == u'RANDOM':
        bot.debug(u'prbooru.py', u'random', u'verbose')
        link = prbooru_search(bot)  # Request a random image else:
    else:
        bot.debug(u'prbooru.py', u'tags', u'verbose')
        link = prbooru_search(bot, tags=tags_list)  # Get image from tags
    if link:
        bot.reply(link)
    elif link is None:
        bot.reply(u"Sorry, the booru is having issues right now...")
    else:
        bot.reply(u"That doesn't seem to exist, maybe you should go tag " +
                  u"a few untagged images..."
                  )


if __name__ == "__main__":
    print __doc__.strip()
