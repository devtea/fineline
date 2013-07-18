"""
timers.py - A Willie module to provide custom timers
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

"""

from time import time
import re
import threading
from types import *
from datetime import timedelta

from willie.module import commands, event, example, interval, rule

_rtime = re.compile(ur'^((\d{1,2}:){1,2})?\d{1,2}$')
_rquiet = re.compile(ur'(^q$)|(^quiet$)|(^p$)|(^private$)', flags=re.I)


def setup(willie):
    if 'user_timers' not in willie.memory:
        willie.memory['user_timers'] = {}
    if 'user_timers_lock' not in willie.memory:
        willie.memory['user_timers_lock'] = threading.Lock()


def format_sec(sec):
    assert type(sec) is FloatType or type(sec) is IntType
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
def new_timer(willie, trigger):
    '''Adds a new personal timer. The first and only requred argument must
 be the duration of the timer of the format 'HH:MM:SS', with hours and minutes
 being optional. To set a reminder, add a second time indicating the time
 remaining for the reminder. Add the word 'quiet' to have the reminder and
 announcement sent in pm.'''
    def parse_time(time_string):
        assert isinstance(time_string, basestring)
        if _rtime.match(time_string):
            times = time_string.split(':')
            if len(times) == 1:
                return int(times[0])
            elif len(times) == 2:
                dur = int(times[0]) * 60 + int(times[1])
                assert type(dur) is IntType
                return dur
            else:
                dur = int(times[0]) * 60 * 60 + \
                    int(times[1]) * 60 + int(times[2])
                assert type(dur) is IntType
                return dur
            assert type(seconds) is IntType
            return seconds
        else:
            raise ValueError(u'Malformed time')

    def add_timer(src, target, end_time_unix, reminder=None, quiet=False):
        # Assume exists willie.memory['user_timers']['source']
        assert isinstance(src, basestring)
        assert isinstance(target, basestring)
        assert type(end_time_unix) is FloatType
        assert type(reminder) is IntType or reminder is None
        assert type(quiet) is BooleanType

        willie.memory['user_timers'][src][target.lower()] = (
            target,
            quiet,
            end_time_unix,
            reminder
        )

    source = trigger.args[0]  # e.g. '#fineline_testing'
    willie.memory['user_timers_lock'].acquire()
    try:
        if source not in willie.memory['user_timers']:
            willie.memory['user_timers'][source] = {}
        if len(trigger.args[1].split()) <= 1:
            willie.reply(
                (u"What timer? Try `%s: help timer` for help") % willie.nick
            )
            return
        if trigger.args[1].split()[1].startswith(u'del'):
            timer_del(willie, trigger)
            return
        if trigger.args[1].split()[1].startswith(u'status'):
            timer_status(willie, trigger)
            return
        if trigger.nick.lower() in willie.memory['user_timers'][source]:
            willie.reply(
                (u"Sorry, %s, you already have a timer running. " +
                    u"Use `!timer del` to remove.") % trigger.nick
            )
            return
        else:
            now = time()
            willie.debug(u'timers_timer.py', u'now = %f' % now, u'verbose')
            possible_timer = trigger.args[1].split()
            willie.debug(u'timers_timer.py', possible_timer, u'verbose')
            if len(possible_timer) > 4:
                willie.reply(
                    (u"Too many arguments! Try `%s: help timer` " +
                        u"for help") % willie.nick
                )
                return
            else:
                willie.debug(u'timers_timer.py', u'POP!', u'verbose')
                __ = possible_timer.pop(0)
                willie.debug(u'timers_timer.py', possible_timer, u'verbose')
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
                    willie.reply(
                        (u"I don't understand! Try `%s: help timer` " +
                            u"for help") % willie.nick
                    )
                    return
                end_time = time() + end
                if not possible_timer:
                    add_timer(source, trigger.nick, end_time)
                    willie.reply(u"Timer added!")
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
                        willie.reply("Your reminder must be shorter than " +
                                     "your timer!")
                        return
                    if not possible_timer:
                        add_timer(
                            source,
                            trigger.nick,
                            end_time,
                            reminder=rem
                        )
                        willie.reply(u"Timer added!")
                        return
                elif _rquiet.match(next_argument):
                    if not possible_timer:
                        add_timer(source, trigger.nick, end_time, quiet=True)
                        willie.reply(u"Timer added! Watch for a /msg.")
                        return
                    qu = True
                else:
                    willie.reply(
                        (u"I don't understand! Try `%s: help timer` " +
                            u"for help") % willie.nick
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
                    willie.reply(u"Timer added! Watch for a /msg.")
                    return
                elif _rquiet.match(next_argument) and not qu:
                    add_timer(
                        source,
                        trigger.nick,
                        end_time,
                        reminder=rem,
                        quiet=True
                    )
                    willie.reply(u"Timer added! Watch for a /msg.")
                    return
                else:
                    willie.reply(
                        (u"I don't understand! Try `%s: help timer` " +
                            u"for help") % willie.nick
                    )
                return
    finally:
        willie.memory['user_timers_lock'].release()


@rule(u'.*')
@event(u'PART')
def auto_quiet_on_part(willie, trigger):
    source = trigger.args[0]
    willie.memory['user_timers_lock'].acquire()
    try:
        if source in willie.memory['user_timers'] and \
                trigger.nick.lower() in willie.memory['user_timers'][source]:
            q, t, r = willie.memory['user_timers'][source][
                trigger.nick.lower()]
            willie.memory['user_timers'][source][trigger.nick.lower()] = (
                True,
                t,
                r
            )
    finally:
        willie.memory['user_timers_lock'].release()


@event(u'QUIT')
@rule(u'.*')
def auto_quiet_on_quit(willie, trigger):
    source = trigger.args[0]
    willie.memory['user_timers_lock'].acquire()
    try:
        if source in willie.memory['user_timers'] and \
                trigger.nick.lower() in willie.memory['user_timers'][source]:
            q, t, r = willie.memory['user_timers'][source][
                trigger.nick.lower()]
            willie.memory['user_timers'][source][trigger.nick.lower()] = (
                True,
                t,
                r
            )
    finally:
        willie.memory['user_timers_lock'].release()


@interval(1)
def timer_check(willie):
    now = time()
    willie.memory['user_timers_lock'].acquire()
    try:
        for chan in willie.memory['user_timers']:
            willie.debug(
                u'timers_timer:timer_check',
                u"found channel %s" % chan,
                u'verbose'
            )
            for user in willie.memory['user_timers'][chan]:
                n, q, e, r = willie.memory['user_timers'][chan][user]
                willie.debug(
                    u'timers_timer:timer_check',
                    u'nick=%s  quiet=%r, time=%f, remind=%r' % (n, q, e, r),
                    u'verbose'
                )
                if e < now:
                    del willie.memory['user_timers'][chan][user]
                    if q:
                        willie.msg(n, u'Time is up!')
                    else:
                        willie.msg(chan, u'%s, time is up!' % n)
                    return
                elif r and r > e - now:
                    willie.memory['user_timers'][chan][user] = (n, q, e, None)
                    if q:
                        willie.msg(
                            n,
                            u'You have %s remaining.' % format_sec(r)
                        )
                    else:
                        willie.msg(
                            chan,
                            u'%s, you have %s remaining.' % (n, format_sec(r))
                        )
    finally:
        willie.memory['user_timers_lock'].release()


def timer_del(willie, trigger):
    # this will be called from new_timer,  assume it is a correct call
    if trigger.admin:
        cmd = trigger.args[1].split()
        willie.debug(u'', cmd, u'verbose')
        if len(cmd) == 2:
            if trigger.nick.lower() in willie.memory['user_timers'][
                    trigger.args[0]]:
                del willie.memory['user_timers'][trigger.args[0]][
                    trigger.nick.lower()]
                willie.reply(u"Your timer has been deleted.")
            else:
                willie.reply(u"You don't have a timer.")
        elif len(cmd) > 2:
            willie.memory['user_timers'] = {}
            willie.reply(u'All timers have been deleted.')
    else:
        if trigger.nick.lower() in willie.memory['user_timers'][
                trigger.args[0]]:
            del willie.memory['user_timers'][trigger.args[0]][
                trigger.nick.lower()]
            willie.reply(u"Your timer has been deleted.")
        else:
            willie.reply(u"You don't have a timer.")


def timer_status(willie, trigger):
    if trigger.nick.lower() in willie.memory['user_timers'][trigger.args[0]]:
        n, q, e, r = willie.memory['user_timers'][trigger.args[0]][
            trigger.nick.lower()]
        willie.debug('', e - time(), 'verbose')
        willie.reply("You have %s remaining." % format_sec(e - time()))
    else:
        willie.reply("You don't have a timer.")


if __name__ == "__main__":
    print __doc__.strip()
