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

_rtime = re.compile(r'^((\d{1,2}:){1,2})?\d{1,2}$')
_rquiet = re.compile(r'(^q$)|(^quiet$)|(^p$)|(^private$)', flags=re.I)

def setup(willie):
    willie.memory['timers_lock'] = threading.Lock()


def format_sec(sec):
    assert type(sec) is FloatType or type(sec) is IntType
    sec = int(round(sec))
    if sec < 60:
        formatted = '%i sec' % sec
        return formatted
    elif sec < 3600:
        mins = sec/60
        sec = sec - mins*60
        formatted = '%i min, %i sec' % (mins, sec)
        return formatted
    else:
        diff = str(timedelta(seconds=sec))
        return diff


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
                dur = int(times[0])*60 + int(times[1])
                assert type(dur) is IntType
                return dur
            else:
                dur = int(times[0])*60*60 + int(times[1])*60 + int(times[2])
                assert type(dur) is IntType
                return dur
            assert type(seconds) is IntType
            return seconds
        else:
            raise ValueError('Malformed time')

    def add_timer(src, target, end_time_unix, reminder=None, quiet=False):
        # Assume exists willie.memory['timers']['timers']['source']
        assert isinstance(src, basestring)
        assert isinstance(target, basestring)
        assert type(end_time_unix) is FloatType
        assert type(reminder) is IntType or reminder is None
        assert type(quiet) is BooleanType

        willie.memory['timers']['timers'][src][target.lower()] = (
                target,
                quiet,
                end_time_unix,
                reminder
                )

    source = trigger.args[0]  # e.g. '#fineline_testing'
    willie.memory['timers_lock'].acquire()
    try:
        if source not in willie.memory['timers']['timers']:
            willie.memory['timers']['timers'][source] = {}
        if trigger.args[1].split()[1].startswith('del'):
            timer_del(willie, trigger)
            return
        if trigger.args[1].split()[1].startswith('status'):
            timer_status(willie, trigger)
            return
        if trigger.nick.lower() in willie.memory['timers']['timers'][source]:
            willie.reply(("Sorry, %s, you already have a timer running. Use " +
                    "`!timer del` to remove.") % trigger.nick)
            return
        else:
            now = time()
            willie.debug('timers_timer.py', 'now = %f' % now, 'verbose')
            possible_timer = trigger.args[1].split()
            willie.debug('timers_timer.py', possible_timer, 'verbose')
            if len(possible_timer) <= 1:
                willie.reply(("What timer? Try `%s: help timer` " +
                        "for help") % willie.nick)
                return
            elif len(possible_timer) > 4:
                willie.reply(("Too many arguments! Try `%s: help timer` " +
                        "for help") % willie.nick)
                return
            else:
                willie.debug('timers_timer.py', 'POP!', 'verbose')
                __ = possible_timer.pop(0)
                willie.debug('timers_timer.py', possible_timer, 'verbose')
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
                    willie.reply(("I don't understand! Try `%s: help timer` " +
                            "for help") % willie.nick)
                    return
                end_time = time()+end
                if not possible_timer:
                    add_timer(source, trigger.nick, end_time)
                    willie.reply("Timer added!")
                    return

                next_argument = possible_timer.pop(0)
                qu = None
                rem = None
                # ["quiet"]
                # ["00:00:00"]
                # []
                if _rtime.match(next_argument):
                    rem = parse_time(next_argument)
                    if not possible_timer:
                        add_timer(source, trigger.nick, end_time, reminder=rem)
                        willie.reply("Timer added!")
                        return
                elif _rquiet.match(next_argument):
                    if not possible_timer:
                        add_timer(source, trigger.nick, end_time, quiet=True)
                        willie.reply("Timer added! Watch for a /msg.")
                        return
                    qu=True
                else:
                    willie.reply(("I don't understand! Try `%s: help timer` " +
                            "for help") % willie.nick)
                    return

                next_argument = possible_timer.pop(0)
                # []
                if _rtime.match(next_argument) and not rem:
                    rem = parse_time(next_argument)
                    add_timer(source, trigger.nick, end_time, reminder=rem, quiet=qu)
                    willie.reply("Timer added! Watch for a /msg.")
                    return
                elif _rquiet.match(next_argument) and not qu:
                    add_timer(source, trigger.nick, end_time, reminder=rem, quiet=True)
                    willie.reply("Timer added! Watch for a /msg.")
                    return
                else:
                    willie.reply(("I don't understand! Try `%s: help timer` " +
                            "for help") % willie.nick)
                return
    finally:
        willie.memory['timers_lock'].release()
new_timer.commands = ["timer", "t"]
new_timer.example = '!timer 01:30:00 quiet 10:00'


def auto_quiet_on_part(willie, trigger):
    source = trigger.args[0]
    willie.memory['timers_lock'].acquire()
    try:
        if source in willie.memory['timers']['timers'] and \
                trigger.nick.lower() in willie.memory['timers']['timers'][source]:
            q, t, r = willie.memory['timers']['timers'][source][trigger.nick.lower()]
            willie.memory['timers']['timers'][source][trigger.nick.lower()] = (True, t, r)
    finally:
        willie.memory['timers_lock'].release()
auto_quiet_on_part.event = 'PART'
auto_quiet_on_part.rule = r'.*'


def auto_quiet_on_quit(willie, trigger):
    source = trigger.args[0]
    willie.memory['timers_lock'].acquire()
    try:
        if source in willie.memory['timers']['timers'] and \
                trigger.nick.lower() in willie.memory['timers']['timers'][source]:
            q, t, r = willie.memory['timers']['timers'][source][trigger.nick.lower()]
            willie.memory['timers']['timers'][source][trigger.nick.lower()] = (True, t, r)
    finally:
        willie.memory['timers_lock'].release()
auto_quiet_on_quit.event = 'QUIT'
auto_quiet_on_quit.rule = r'.*'


def timer_check(willie):
    willie.memory['timers_lock'].acquire()
    try:
        if 'timers' not in willie.memory['timers']:
            willie.memory['timers']['timers'] = {}
    except KeyError:
        raise
    now = time()
    willie.debug('timers_timer:timer_check', 'now = %f' % now, 'verbose')
    try:
        for chan in willie.memory['timers']['timers']:
            willie.debug('timers_timer:timer_check', "found channel %s" % chan, 'verbose')
            for user in willie.memory['timers']['timers'][chan]:
                n, q, e, r = willie.memory['timers']['timers'][chan][user]
                willie.debug(
                        'timers_timer:timer_check',
                        'nick=%s  quiet=%r, time=%f, remind=%r' % ( n, q, e, r),
                        'verbose'
                        )
                if e < now:
                    del willie.memory['timers']['timers'][chan][user]
                    if q:
                        willie.msg(n, 'Time is up!') #handle caps?
                    else:
                        willie.msg(chan, '%s, time is up!' % n)
                    return
                elif r and r > e-now:
                    willie.memory['timers']['timers'][chan][user] = (n, q, e, None)
                    if q:
                        willie.msg(n, 'You have %s remaining.' % format_sec(r))
                    else:
                        willie.msg(chan, '%s, you have %s remaining.' % (n, format_sec(r)))
    finally:
        willie.memory['timers_lock'].release()


def timer_del(willie, trigger):
    # this will be called from new_timer,  assume it is a correct call
    if trigger.admin:
        cmd = trigger.args[1].split()
        willie.debug('',cmd,'verbose')
        if len(cmd) == 2:
            if trigger.nick.lower() in willie.memory['timers']['timers'][trigger.args[0]]:
                del willie.memory['timers']['timers'][trigger.args[0]][trigger.nick.lower()]
                willie.reply("Your timer has been deleted.")
            else:
                willie.reply("You don't have a timer.")
        elif len(cmd) > 2:
            willie.memory['timers']['timers'] = {}
            willie.reply('All timers have been deleted.')
    else:
        if trigger.nick.lower() in willie.memory['timers']['timers'][trigger.args[0]]:
            del willie.memory['timers']['timers'][trigger.args[0]][trigger.nick.lower()]
            willie.reply("Your timer has been deleted.")
        else:
            willie.reply("You don't have a timer.")


def timer_status(willie, trigger):
    if trigger.nick.lower() in willie.memory['timers']['timers'][trigger.args[0]]:
        n, q, e, r = willie.memory['timers']['timers'][trigger.args[0]][trigger.nick.lower()]
        willie.debug('', e-time(), 'verbose')
        willie.reply("You have %s remaining." % format_sec(e-time()))
    else:
        willie.reply("You don't have a timer.")



if __name__ == "__main__":
    print __doc__.strip()
