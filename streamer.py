"""
streamer.py - A simple willie module to stream recorded video to justin.tv
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import os
import re
import subprocess
import textwrap
import time
from collections import deque

from willie.module import commands, example, interval

_CHAN_EXC = []


def setup(bot):
    if 'streaming' not in bot.memory:
        bot.memory['streaming'] = {}
    bot.memory['streaming']['jtv_key'] = bot.config.streaming.jtv_key
    bot.memory['streaming']['source_dir'] = bot.config.streaming.source_dir
    bot.memory['streaming']['loc'] = bot.config.streaming.stream_loc
    if 'live' not in bot.memory['streaming']:
        bot.memory['streaming']['live'] = False
    if 'deque' not in bot.memory['streaming']:
        bot.memory['streaming']['deque'] = deque()
    try:
        file_list = os.listdir(bot.memory['streaming']['source_dir'])
    except OSError:
        bot.debug('streamer.py', 'Unable to load list of files.', 'warning')
        raise
    else:
        file_list.sort()
        bot.memory['streaming']['ep_list'] = file_list


@interval(2)
def queue_watcher(bot, trigger=None):
    if bot.memory['streaming']['live']:
        return
    if bot.memory['streaming']['deque']:
        start_stream(bot, bot.memory['streaming']['deque'].popleft())


def start_stream(bot, ep):
    for channel in bot.channels:
        if channel in _CHAN_EXC:
            continue
        bot.msg(
            channel,
            u'Starting stream of %s at %s.' % (
                ep,
                bot.memory['streaming']['loc']
            )
        )
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
    '''Adds or removes a video from the streaming queue. Use "!stream add
 <name>" to add a video, or "!stream del <name>" to remove it. Do
 "!stream list" for a list of available videos. Do "!stream queue" to
 see the videos queued for streaming.'''
    def scrub(i):
        '''Scrub input for safe REGEX'''
        return re.sub(u'[\\\.\?|^$*+([{]', u'', i)

    def process(name):
        '''Processes provided video name.'''
        arg_ep = name
        # First check for simple matches.
        if arg_ep in [os.path.splitext(i)[0].upper() for i
                      in bot.memory['streaming']['ep_list']]:
            # To account for varied case in filenames, we need to get the right
            # name from the list of good filenames.
            index = [os.path.splitext(i)[0].upper()
                     for i in bot.memory['streaming']['ep_list']].index(arg_ep)
            arg_ep = os.path.splitext(bot.memory['streaming']['ep_list'].pop(
                index))[0]
            enqueue(bot, arg_ep)
        # Next check for regexable strings
        elif len(arg_ep) == 6:
            arg_ep = scrub(arg_ep)
            if len(arg_ep) < 6:
                bot.reply(u"Sorry, I don't seem to have that.")
                return
            a, b = (arg_ep[0:3], arg_ep[3:6])
            re_eps = re.compile(u'%s(?:...)?%s(?:...)?' % (a, b))
            results = [m.group(0) for e in bot.memory['streaming']['ep_list']
                       for m in [re_eps.search(os.path.splitext(e)[0])] if m]
            if results:
                arg_ep = results[0]
                enqueue(bot, arg_ep)
            else:
                bot.reply(u"Sorry, I don't seem to have that.")
                return  # TODO is this really necessary?
        else:
            bot.reply(u"Sorry, I don't seem to have that.")
            return  # TODO is this really necessary?

    if len(trigger.args[1].split()) == 2:  # E.G. "!stream s01e01"
        arg_1 = trigger.args[1].split()[1].upper()
        if arg_1 == u'QUEUE' or arg_1 == u'QUE':
            get_queue(bot)
        elif arg_1 == u'LIST':
            list_media(bot, trigger)
        else:
            process(arg_1)
    elif len(trigger.args[1].split()) == 3:  # E.G. "!stream add s01e01"
        arg_1 = trigger.args[1].split()[1].upper()
        arg_2 = trigger.args[1].split()[2].upper()
        if arg_1 == u'ADD':
            process(arg_2)
        elif arg_1 == u'DEL':
            dequeue(bot, arg_2)
        else:
            bot.debug(u"episodes.py:episode", u"insane args", u"verbose")
            bot.reply(u"I don't understand that. Try '%s: help " % bot.nick +
                      u"streamer'")
    elif len(trigger.args[1].split()) > 3:
        bot.debug(u"episodes.py:episode", u"too many args", u"verbose")
        bot.reply(u"I don't understand that. Try '%s: help " % bot.nick +
                  u"streamer'")
    else:
        bot.reply(u'Stream what?! See the help for details.')
        bot.debug(u"episodes.py:episode", u"Not enough args", u"verbose")
        bot.reply(u"I don't understand that. Try '%s: help " % bot.nick +
                  u"streamer'")


def enqueue(bot, ep):
    '''Adds a video to the queue.'''
    if len(bot.memory['streaming']['deque']) <= 3:
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
    bot.reply(u'Sending you the list in PM.')
    for line in textwrap.wrap(
            u'Available videos: %s' % ', '.join(
                [os.path.splitext(i)[0]
                    for i in bot.memory['streaming']['ep_list']]),
            200):
        bot.msg(trigger.nick, line)


@commands('streaming', 'now_playing', 'np', 'now_streaming', 'ns')
def streaming(bot, trigger):
    '''To manage videos or get information, see !stream.'''
    if bot.memory['streaming']['live']:
        bot.reply(u'Now plaing at %s - %s' % (
            bot.memory['streaming']['loc'],
            bot.memory['streaming']['title'],
        ))
    else:
        bot.reply(u'Nothing streaming right now.')


if __name__ == "__main__":
    print __doc__.strip()
