# coding=utf8
"""
tell.py - Willie Tell and Ask Module
Copyright 2008, Sean B. Palmer, inamidst.com, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
import os.path
import sys
import time
import threading

import willie.tools
from willie.logger import get_logger
from willie.tools import Identifier, iterkeys
from willie.module import commands, nickname_commands, rule, priority, example

LOGGER = get_logger(__name__)

maximum = 4

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    # import sys
    # import os.path
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()
try:
    import nicks
except:
    import imp
    # import sys
    # import os.path
    try:
        LOGGER.info(log.format("trying manual import of nicks"))
        fp, pathname, description = imp.find_module('nicks', [os.path.join('.', '.willie', 'modules')])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()
try:
    import util
except:
    import imp
    # import sys
    # import os.path
    try:
        LOGGER.info(log.format("trying manual import of util"))
        fp, pathname, description = imp.find_module('util', [os.path.join('.', '.willie', 'modules')])
        util = imp.load_source('util', pathname, fp)
        sys.modules['util'] = util
    finally:
        if fp:
            fp.close()


def loadReminders(fn, lock):
    with lock:
        result = {}
        f = open(fn)
        for line in f:
            line = line.strip()
            if sys.version_info.major < 3:
                line = line.decode('utf-8')
            if line:
                try:
                    tellee, teller, verb, timenow, msg = line.split('\t', 4)
                except ValueError:
                    continue  # @@ hmm
                result.setdefault(tellee, []).append((teller, verb, timenow, msg))
        f.close()
    return result


def dumpReminders(fn, data, lock):
    with lock:
        f = open(fn, 'w')
        for tellee in iterkeys(data):
            for remindon in data[tellee]:
                line = '\t'.join((tellee,) + remindon)
                try:
                    to_write = line + '\n'
                    if sys.version_info.major < 3:
                        to_write = to_write.encode('utf-8')
                    f.write(to_write)
                except IOError:
                    break
        try:
            f.close()
        except IOError:
            pass
    return True


def setup(self):
    fn = self.nick + '-' + self.config.host + '.tell.db'
    self.tell_filename = os.path.join(self.config.dotdir, fn)
    if not os.path.exists(self.tell_filename):
        try:
            f = open(self.tell_filename, 'w')
        except OSError:
            pass
        else:
            f.write('')
            f.close()
    self.memory['tell_lock'] = threading.Lock()
    self.memory['reminders'] = loadReminders(self.tell_filename, self.memory['tell_lock'])


@commands('tell', 'ask')
@nickname_commands('tell', 'ask')
@example('!tell some_user butts are cool.')
def f_remind(bot, trigger):
    """Give someone a message the next time they're seen"""
    # Filter when certain other bots are present
    if util.exists_quieting_nick(bot, trigger.sender):
        return

    # Don't let people send in PMs
    if not trigger.sender.startswith('#'):
        return

    teller = trigger.nick
    verb = trigger.group(1)

    if not trigger.group(3):
        bot.reply("%s whom?" % verb)
        return

    tellee = trigger.group(3).rstrip('.,:;')
    msg = trigger.group(2).lstrip(tellee).lstrip()

    if not msg:
        bot.reply("%s %s what?" % (verb, tellee))
        return

    tellee = Identifier(tellee)

    if not os.path.exists(bot.tell_filename):
        return

    if len(tellee) > 20:
        return bot.reply('That nickname is too long.')
    if tellee == bot.nick:
        return bot.reply("I'm here now, you can tell me whatever you want!")

    if tellee not in (Identifier(teller), bot.nick, 'me'):
        tz = willie.tools.get_timezone(bot.db, bot.config, None, tellee)
        timenow = willie.tools.format_time(bot.db, bot.config, tz, tellee)
        with bot.memory['tell_lock']:
            if tellee not in bot.memory['reminders']:
                bot.memory['reminders'][tellee] = [(teller, verb, timenow, msg)]
            else:
                bot.memory['reminders'][tellee].append((teller, verb, timenow, msg))

        response = "I'll pass that on when %s is around." % tellee

        bot.reply(response)
    elif Identifier(teller) == tellee:
        bot.say('You can %s yourself that.' % verb)
    else:
        bot.say("Hey, I'm not as stupid as Monty you know!")

    dumpReminders(bot.tell_filename, bot.memory['reminders'], bot.memory['tell_lock'])  # @@ tell


def getReminders(bot, channel, key, tellee):
    lines = []
    template = "%s: %s <%s> %s"
    today = time.strftime('%d %b', time.gmtime())

    with bot.memory['tell_lock']:
        for (teller, verb, datetime, msg) in bot.memory['reminders'][key]:
            if datetime.startswith(today):
                datetime = datetime[len(today) + 1:]
            # lines.append(template % (tellee, datetime, teller, verb, tellee, msg))
            lines.append(template % (tellee, datetime, teller, msg))

        try:
            del bot.memory['reminders'][key]
        except KeyError:
            bot.msg(channel, 'Er...')
    return lines


@rule('(.*)')
@priority('low')
def message(bot, trigger):

    tellee = trigger.nick
    channel = trigger.sender

    if not os.path.exists(bot.tell_filename):
        return

    reminders = []
    remkeys = list(reversed(sorted(bot.memory['reminders'].keys())))

    for remkey in remkeys:
        if not remkey.endswith('*') or remkey.endswith(':'):
            if tellee == remkey:
                reminders.extend(getReminders(bot, channel, remkey, tellee))
        elif tellee.startswith(remkey.rstrip('*:')):
            reminders.extend(getReminders(bot, channel, remkey, tellee))

    for line in reminders[:maximum]:
        bot.say(line)

    if reminders[maximum:]:
        bot.say('Further messages sent privately')
        for line in reminders[maximum:]:
            bot.msg(tellee, line)

    if len(bot.memory['reminders'].keys()) != remkeys:
        dumpReminders(bot.tell_filename, bot.memory['reminders'], bot.memory['tell_lock'])  # @@ tell


if __name__ == "__main__":
    print(__doc__.strip())
