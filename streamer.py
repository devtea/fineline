"""
streamer.py - A simple willie module to stream recorded video to justin.tv
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

from collections import deque
import os
import random
import re
from string import Template
import subprocess
import textwrap
import time

from willie.module import commands, example, interval

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

_include = ['#reddit-mlpds', '#fineline_testing']
# TODO Config section to set up config options


def setup(bot):
    if 'streaming' not in bot.memory:
        bot.memory['streaming'] = {}
    bot.memory['streaming']['jtv_key'] = bot.config.streaming.jtv_key
    bot.memory['streaming']['source_dir'] = bot.config.streaming.source_dir
    bot.memory['streaming']['loc'] = bot.config.streaming.stream_loc
    bot.memory['streaming']['custom_regex'] = re.compile(bot.config.streaming.custom_regex)
    bot.memory['streaming']['template'] = bot.config.streaming.list_template
    bot.memory['streaming']['dest'] = bot.config.streaming.list_dest
    bot.memory['streaming']['url'] = bot.config.streaming.list_url
    bot.memory['streaming']['use_html'] = False
    if bot.config.has_option('streaming', 'use_html'):
        if bot.config.streaming.use_html == 'True':
            bot.memory['streaming']['use_html'] = True
    if 'live' not in bot.memory['streaming']:
        bot.memory['streaming']['live'] = False
    if 'deque' not in bot.memory['streaming']:
        bot.memory['streaming']['deque'] = deque()
    try:
        file_list = os.listdir(bot.memory['streaming']['source_dir'])
    except OSError:
        bot.debug(__file__, log.format('Unable to load list of files.'), 'warning')
        raise
    else:
        file_list.sort()
        bot.memory['streaming']['ep_list'] = file_list
    with open(bot.memory['streaming']['template']) as f:
        try:
            bot.memory['streaming']['listTemplate'] = Template(f.read())
        except:
            bot.debug(__file__, log.format(u'Unable to load template.'), u'always')
            raise
    publish_list(bot)


@interval(2)
def queue_watcher(bot, trigger=None):
    if bot.memory['streaming']['live']:
        return
    if bot.memory['streaming']['deque']:
        start_stream(bot, bot.memory['streaming']['deque'].popleft())


def start_stream(bot, ep):
    for channel in [x for x in bot.channels if x in _include]:
        bot.msg(
            channel,
            u'Starting stream of %s at %s' % (
                ep,
                bot.memory['streaming']['loc']
            )
        )
    bot.debug(__file__, log.format('streamer.py Starting stream of %s' % ep), 'always')
    bot.memory['streaming']['live'] = True
    bot.memory['streaming']['title'] = ep
    try:
        subprocess.call(
            u"avconv -re -i " +
            u"%s" % bot.memory['streaming']['source_dir'] +
            u"%s.flv -acodec copy -vcodec copy " % ep +
            u"-f flv rtmp://live.justin.tv/app/" +
            u"%s" % bot.memory['streaming']['jtv_key'],
            shell=True
        )
    finally:
        time.sleep(15)
        bot.memory['streaming']['live'] = False


@example('!stream add S01E03')
@commands('stream')
def stream(bot, trigger):
    '''Adds or removes a video from the stream queue. Use "!stream add
 <name>" to add a video, or "!stream del <name>" to remove it. Do
 "!stream list" for a list of available videos. Do "!stream queue" to
 see the videos queued for streaming.'''
    def scrub(i):
        '''Scrub input for safe REGEX'''
        return re.sub(u'[\\\.\?|^$*+([{]', u'', i)

    def process(name):
        '''returns a normalized video name.'''
        arg_ep = name
        # First check for simple matches.
        if arg_ep in [os.path.splitext(i)[0].upper() for i
                      in bot.memory['streaming']['ep_list']]:
            # To account for varied case in filenames, we need to get the right
            # name from the list of good filenames.
            index = [os.path.splitext(i)[0].upper()
                     for i in bot.memory['streaming']['ep_list']].index(arg_ep)
            arg_ep = os.path.splitext(bot.memory['streaming']['ep_list'
                                                              ][index])[0]
            return arg_ep
        else:
            return None

    if len(trigger.args[1].split()) == 2:  # E.G. "!stream s01e01"
        arg_1 = trigger.args[1].split()[1].upper()
        if arg_1 == u'QUEUE' or arg_1 == u'QUE':
            get_queue(bot)
        elif arg_1 == u'LIST':
            list_media(bot, trigger)
        else:
            enqueue(bot, process(arg_1))
    elif len(trigger.args[1].split()) == 3:  # E.G. "!stream add s01e01"
        arg_1 = trigger.args[1].split()[1].upper()
        arg_2 = trigger.args[1].split()[2].upper()
        if arg_1 == u'ADD':
            enqueue(bot, process(arg_2))
        elif arg_1 == u'DEL':
            dequeue(bot, process(arg_2))
        else:
            bot.debug(__file__, log.format(u"insane args"), u"verbose")
            bot.reply(u"I don't understand that. Try '%s: help " % bot.nick +
                      u"stream'")
    elif len(trigger.args[1].split()) > 3:
        bot.debug(__file__, log.format(u"too many args"), u"verbose")
        bot.reply(u"I don't understand that. Try '%s: help " % bot.nick +
                  u"stream'")
    else:
        bot.reply(u'Stream what?! Try !help stream for details.')
        bot.debug(__file__, log.format(u"Not enough args"), u"verbose")


def enqueue(bot, ep):
    '''Adds a video to the queue.'''
    if not ep:
        bot.reply(u"Sorry, I don't seem to have that.")
        return
    if len(bot.memory['streaming']['deque']) <= 4:
        bot.memory['streaming']['deque'].append(ep)
        bot.say(u'Added %s to the queue.' % ep)
    else:
        bot.reply(u"Sorry, the queue is full.")


def dequeue(bot, video):
    '''Removes a video from the queue.'''
    try:
        bot.memory['streaming']['deque'].remove(video)
    except ValueError:
        bot.reply(u"I don't have that in my queue.")
    else:
        bot.reply(u"%s removed." % video)


def promote():
    '''Moves a video up one spot in the queue.'''
    # TODO
    return


def demote():
    '''Moves a video down one spot in the queue.'''
    # TODO
    return


def get_queue(bot):
    if len(bot.memory['streaming']['deque']) == 0:
        bot.reply(u'The stream queue is currently empty.')
    else:
        bot.reply(u'Currently queued: %s' % ', '.join(
            bot.memory['streaming']['deque'])
        )


def list_media(bot, trigger):
    bot.debug(__file__, log.format(log.format(bot.memory['streaming']['use_html'])), 'verbose')
    if bot.memory['streaming']['use_html']:
        bot.reply(u'The list of available videos is up at %s' %
                  bot.memory['streaming']['url'])
    else:
        bot.reply(u'Sending you the list in PM.')
        for line in textwrap.wrap(
                u'Available videos: %s' % ', '.join(
                    [os.path.splitext(i)[0]
                        for i in bot.memory['streaming']['ep_list']]),
                390):
            bot.msg(trigger.nick, line)


@commands('streaming', 'now_playing', 'np', 'now_streaming', 'ns')
def streaming(bot, trigger):
    '''Lists the currently streaming video. To manage videos or get information, see !stream.'''
    if bot.memory['streaming']['live']:
        bot.reply(u'Now playing at %s - %s' % (
            bot.memory['streaming']['loc'],
            bot.memory['streaming']['title'],
        ))
    else:
        bot.reply(u'Nothing streaming right now.')


def publish_list(bot):
    if not bot.memory['streaming']['use_html']:
        return
    bot.debug(__file__, log.format(log.format(bot.memory['streaming']['dest'])), 'verbose')
    try:
        with open(bot.memory['streaming']['dest'], 'r') as f:
            previous_full_list = ''.join(f.readlines())
    except IOError:
        previous_full_list = ''
        bot.debug(
            __file__,
            log.format(u'IO error grabbing "list_main_dest_path" file contents. File may not exist yet'),
            u'warning')

    # Generate full list HTML
    contents = bot.memory['streaming']['listTemplate'].substitute(
        ulist='\n'.join(
            ['<li>%s</li>' % os.path.splitext(i)[0] for i in bot.memory['streaming']['ep_list']]
        ))
    # Don't clobber the HDD
    if previous_full_list != contents:
        with open(bot.memory['streaming']['dest'], 'w') as f:
            f.write(contents)
    else:
        bot.debug(__file__, log.format(u'No chage in list html file, skipping.'), u'verbose')
    return


@commands('bob')
def random_video(bot, trigger):
    '''Getcho Bob fix here!'''
    match_list = [os.path.splitext(i)[0] for i in bot.memory['streaming']['ep_list']
                  if bot.memory['streaming']['custom_regex'].match(i)]
    enqueue(bot, random.choice(match_list))


if __name__ == "__main__":
    print(__doc__.strip())
