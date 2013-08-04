"""
streamer.py - A simple willie module to stream recorded video to justin.tv
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import os
import re
import subprocess

from willie.module import commands


def setup(bot):
    if 'streaming' not in bot.memory:
        bot.memory['streaming'] = {}
    bot.memory['streaming']['jtv_key'] = bot.config.streaming.jtv_key
    bot.memory['streaming']['source_dir'] = bot.config.streaming.source_dir
    bot.memory['streaming']['loc'] = bot.config.streaming.stream_loc
    if 'live' not in bot.memory['streaming']:
        bot.memory['streaming']['live'] = False
    try:
        file_list = os.listdir(bot.memory['streaming']['source_dir'])
    except OSError:
        bot.debug('streamer.py', 'Unable to load list of files.', 'verbose')
        raise
    else:
        bot.memory['streaming']['ep_list'] = file_list


def start_stream():
    # TODO
    pass


@commands('now_playing')
def check_stream():
    # TODO
    pass


@commands('stream')
def enqueue(bot, trigger):
    # TODO
    #test the arguments returned, e.g. ['.stream', 'S01E03']
    try:
        arg_ep = trigger.args[1].split()[1].upper()
    except IndexError:
        bot.debug(u"episodes.py:episode", u"Not enough args", u"verbose")
        bot.reply(u"I don't understand that. Try '%s: help " % bot.nick +
                  u"streamer'")
        return
    if len(trigger.args[1].split()) == 2:
        #Test the second argument for sanity, eg 'S01E03'
        #if re.match(ur'^S\d{1,2}E\d{1,2}$',
        #            arg_ep,
        #            flags=re.IGNORECASE
        #            ):
        #    bot.debug(u"episodes.py:episode",
        #              u"Argument is sane",
        #              u"verbose"
        #              )
        if arg_ep in [os.path.splitext(i)[0] for i
                      in bot.memory['streaming']['ep_list']]:
            if bot.memory['streaming']['live']:
                bot.reply('Sorry, alreading streaming something.')
            else:
                bot.reply(u'Starting stream of %s at %s.' % (
                    arg_ep,
                    bot.memory['streaming']['loc']
                ))
                bot.memory['streaming']['live'] = True
                try:
                    subprocess.call(
                        u"avconv -re -i " +
                        u"%s" % bot.memory['streaming']['source_dir'] +
                        u"%s.flv -acodec copy -vcodec copy " % arg_ep +
                        u"-f flv rtmp://live.justin.tv/app/" +
                        u"%s" % bot.memory['streaming']['jtv_key'],
                        shell=True
                    )
                finally:
                    bot.memory['streaming']['live'] = False
        else:
            bot.reply(u"Sorry, I don't seem to have that.")
            return  # TODO is this really necessary?
        #else:
        #    bot.debug(u"stream.py",
        #              u"Argument is insane",
        #              u"verbose"
        #              )
        #    bot.reply(u"I don't understand that. Try '%s: help " % bot.nick +
        #            u"streamer'")
    elif len(trigger.args[1].split()) > 2:
        bot.debug(u"episodes.py:episode", u"too many args", u"verbose")
        bot.reply(u"I don't understand that. Try '%s: help " % bot.nick +
                  u"streamer'")
        #randep(bot, trigger)


def dequeue():
    # TODO
    pass


def get_queue():
    # TODO
    pass


def list_media():
    # TODO
    pass


if __name__ == "__main__":
    print __doc__.strip()
