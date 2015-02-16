"""
timers.py - A willie module to provide custom timers
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

"""
from datetime import timedelta
import re
import threading
from time import time

from willie.logger import get_logger
from willie.module import commands, event, example, interval, rule

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

_rtime = re.compile(r'^((\d{1,2}:){1,2})?\d{1,2}$')
_rquiet = re.compile(r'(^q$)|(^quiet$)|(^p$)|(^private$)', flags=re.I)


def setup(bot):
    if 'user_timers' not in bot.memory:
        bot.memory['user_timers'] = {}
    if 'user_timers_lock' not in bot.memory:
        bot.memory['user_timers_lock'] = threading.Lock()


def format_sec(sec):
    assert isinstance(sec, float) or isinstance(sec, int)
    sec = int(round(sec))
    if sec < 60:
        formatted = '%i sec' % sec
        return formatted
    elif sec < 3600:
        mins = sec / 60
        sec = sec - mins * 60
        formatted = '%i min, %i sec' % (mins, sec)
        return formatted
    else:
        diff = str(timedelta(seconds=sec))
        return diff


@commands("timer", "t")
@example('!timer 01:30:00 quiet 10:00')
def new_timer(bot, trigger):
    '''Adds a new personal timer. The first and only requred argument must
 be the duration of the timer of the format 'HH:MM:SS', with hours and minutes
 being optional. To set a reminder, add a second time indicating the time
 remaining for the reminder. Add the word 'quiet' to have the reminder and
 announcement sent in pm.'''
    def parse_time(time_string):
        assert isinstance(time_string, str)
        if _rtime.match(time_string):
            times = time_string.split(':')
            if len(times) == 1:
                return int(times[0])
            elif len(times) == 2:
                dur = int(times[0]) * 60 + int(times[1])
                assert isinstance(dur, int)
                return dur
            else:
                dur = int(times[0]) * 60 * 60 + \
                    int(times[1]) * 60 + int(times[2])
                assert isinstance(dur, int)
                return dur
        else:
            raise ValueError('Malformed time')

    def add_timer(src, target, end_time_unix, reminder=None, quiet=False):
        # Assume exists bot.memory['user_timers']['source']
        assert isinstance(src, str)
        assert isinstance(target, str)
        assert isinstance(end_time_unix, float)
        assert isinstance(reminder, int) or reminder is None
        assert isinstance(quiet, bool)

        bot.memory['user_timers'][src][target.lower()] = (
            target,
            quiet,
            end_time_unix,
            reminder
        )

    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    source = trigger.args[0]  # e.g. '#fineline_testing'
    with bot.memory['user_timers_lock']:
        if source not in bot.memory['user_timers']:
            bot.memory['user_timers'][source] = {}
        if len(trigger.args[1].split()) <= 1:
            bot.reply(
                ("What timer? Try `%s: help timer` for help") % bot.nick
            )
            return
        if trigger.args[1].split()[1].startswith('del'):
            timer_del(bot, trigger)
            return
        if trigger.args[1].split()[1].startswith('status'):
            timer_status(bot, trigger)
            return
        if trigger.nick.lower() in bot.memory['user_timers'][source]:
            bot.reply(
                ("Sorry, %s, you already have a timer running. " +
                    "Use `!timer del` to remove.") % trigger.nick
            )
            return
        else:
            now = time()
            LOGGER.info(log.format('now = %f'), now)
            possible_timer = trigger.args[1].split()
            LOGGER.info(log.format(possible_timer))
            if len(possible_timer) > 4:
                bot.reply(
                    ("Too many arguments! Try `%s: help timer` " +
                        "for help") % bot.nick
                )
                return
            else:
                LOGGER.debug(log.format('POP!'))
                possible_timer.pop(0)
                LOGGER.info(log.format(possible_timer))
                # ["00:00:00", "00:00:00", "quiet"]
                # ["00:00:00", "quiet", "00:00:00"]
                # ["00:00:00", "00:00:00"]
                # ["00:00:00", "quiet"]
                # ["00:00:00"]
                # ["del[ete]", "all"]
                duration = possible_timer.pop(0)
                # ["00:00:00", "quiet"]
                # ["quiet", "00:00:00"]
                # ["00:00:00"]
                # ["quiet"]
                # []
                try:
                    end = parse_time(duration)
                except ValueError:
                    bot.reply(
                        ("I don't understand! Try `%s: help timer` " +
                            "for help") % bot.nick
                    )
                    return
                end_time = time() + end
                if not possible_timer:
                    add_timer(source, trigger.nick, end_time)
                    bot.reply("Timer added!")
                    return

                next_argument = possible_timer.pop(0)
                qu = None
                rem = None
                # ["quiet"]
                # ["00:00:00"]
                # []
                if _rtime.match(next_argument):
                    rem = parse_time(next_argument)
                    if rem >= end:
                        bot.reply("Your reminder must be shorter than your timer!")
                        return
                    if not possible_timer:
                        add_timer(
                            source,
                            trigger.nick,
                            end_time,
                            reminder=rem
                        )
                        bot.reply("Timer added!")
                        return
                elif _rquiet.match(next_argument):
                    if not possible_timer:
                        add_timer(source, trigger.nick, end_time, quiet=True)
                        bot.reply("Timer added! Watch for a /msg.")
                        return
                    qu = True
                else:
                    bot.reply(
                        ("I don't understand! Try `%s: help timer` " +
                            "for help") % bot.nick
                    )
                    return

                next_argument = possible_timer.pop(0)
                # []
                if _rtime.match(next_argument) and not rem:
                    rem = parse_time(next_argument)
                    add_timer(
                        source,
                        trigger.nick,
                        end_time,
                        reminder=rem,
                        quiet=qu
                    )
                    bot.reply("Timer added! Watch for a /msg.")
                    return
                elif _rquiet.match(next_argument) and not qu:
                    add_timer(
                        source,
                        trigger.nick,
                        end_time,
                        reminder=rem,
                        quiet=True
                    )
                    bot.reply("Timer added! Watch for a /msg.")
                    return
                else:
                    bot.reply(
                        ("I don't understand! Try `%s: help timer` " +
                            "for help") % bot.nick
                    )
                return


@rule('.*')
@event('PART')
def auto_quiet_on_part(bot, trigger):
    source = trigger.args[0]
    with bot.memory['user_timers_lock']:
        if source in bot.memory['user_timers'] and \
                trigger.nick.lower() in bot.memory['user_timers'][source]:
            n, q, t, r = bot.memory['user_timers'][source][
                trigger.nick.lower()]
            bot.memory['user_timers'][source][trigger.nick.lower()] = (
                n,
                True,
                t,
                r
            )


@event('QUIT')
@rule('.*')
def auto_quiet_on_quit(bot, trigger):
    source = trigger.args[0]
    with bot.memory['user_timers_lock']:
        if source in bot.memory['user_timers'] and \
                trigger.nick.lower() in bot.memory['user_timers'][source]:
            n, q, t, r = bot.memory['user_timers'][source][
                trigger.nick.lower()]
            bot.memory['user_timers'][source][trigger.nick.lower()] = (
                n,
                True,
                t,
                r
            )


@interval(1)
def timer_check(bot):
    now = time()
    with bot.memory['user_timers_lock']:
        for chan in bot.memory['user_timers']:
            LOGGER.debug(log.format("found channel %s"), chan)
            for user in bot.memory['user_timers'][chan]:
                n, q, e, r = bot.memory['user_timers'][chan][user]
                LOGGER.debug(log.format('nick=%s  quiet=%r, time=%f, remind=%r'), n, q, e, r)
                if e < now:
                    del bot.memory['user_timers'][chan][user]
                    if q:
                        bot.msg(n, 'Time is up!')
                    else:
                        bot.msg(chan, '%s, time is up!' % n)
                    return
                elif r and r > e - now:
                    bot.memory['user_timers'][chan][user] = (n, q, e, None)
                    if q:
                        bot.msg(
                            n,
                            'You have %s remaining.' % format_sec(r)
                        )
                    else:
                        bot.msg(
                            chan,
                            '%s, you have %s remaining.' % (n, format_sec(r))
                        )


def timer_del(bot, trigger):
    # this will be called from new_timer,  assume it is a correct call
    if trigger.admin:
        cmd = trigger.args[1].split()
        LOGGER.info(log.format(cmd))
        if len(cmd) == 2:
            if trigger.nick.lower() in bot.memory['user_timers'][
                    trigger.args[0]]:
                del bot.memory['user_timers'][trigger.args[0]][
                    trigger.nick.lower()]
                bot.reply("Your timer has been deleted.")
            else:
                bot.reply("You don't have a timer.")
        elif len(cmd) > 2:
            bot.memory['user_timers'] = {}
            bot.reply('All timers have been deleted.')
    else:
        if trigger.nick.lower() in bot.memory['user_timers'][
                trigger.args[0]]:
            del bot.memory['user_timers'][trigger.args[0]][
                trigger.nick.lower()]
            bot.reply("Your timer has been deleted.")
        else:
            bot.reply("You don't have a timer.")


def timer_status(bot, trigger):
    if trigger.nick.lower() in bot.memory['user_timers'][trigger.args[0]]:
        n, q, e, r = bot.memory['user_timers'][trigger.args[0]][
            trigger.nick.lower()]
        LOGGER.info(log.format(e - time()))
        bot.reply("You have %s remaining." % format_sec(e - time()))
    else:
        bot.reply("You don't have a timer.")


if __name__ == "__main__":
    print(__doc__.strip())
