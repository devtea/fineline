"""
karma.py - A willie module to keep track of "points" for arbitrary things
Copyright 2013, Khyperia, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function
from __future__ import unicode_literals

import csv
import json
import os.path
import threading
import time

from string import Template
from pprint import pprint

from willie.module import commands, example, rule, priority, rate
from willie.formatting import color

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
try:
    import util
except:
    import imp
    import sys
    try:
        print("trying manual import of util")
        fp, pathname, description = imp.find_module('util', [os.path.join('.', '.willie', 'modules')])
        util = imp.load_source('util', pathname, fp)
        sys.modules['util'] = util
    finally:
        if fp:
            fp.close()
try:
    import nicks
except:
    import imp
    import sys
    try:
        print("trying manual import of nicks")
        fp, pathname, description = imp.find_module('nicks', [os.path.join('.', '.willie', 'modules')])
        nicks = imp.load_source('nicks', pathname, fp)
        sys.modules['nicks'] = nicks
    finally:
        if fp:
            fp.close()

SMALL_WAIT_MULTIPLIER = 1.1


def setup(bot):
    if bot.config.has_section('karma') and bot.config.has_option('karma', 'export_dir'):
        bot.memory['karma_export_dir'] = bot.config.karma.export_dir
        bot.memory['karma_url'] = bot.config.karma.url
    else:
        bot.memory['karma_export_dir'] = None
    bot.memory
    if 'karma_lock' not in bot.memory:
        bot.memory['karma_lock'] = threading.Lock()

    with bot.memory['karma_lock']:
        bot.memory['karma_time'] = {}
        bot.memory['karma'] = {}

        dbcon = bot.db.connect()  # sqlite3 connection
        cur = dbcon.cursor()
        try:
            # if our tables don't exist, create them
            cur.execute('''CREATE TABLE IF NOT EXISTS karma
                           (tag text, score int)''')
            dbcon.commit()

            cur.execute('SELECT tag, score from karma')
            dbload = cur.fetchall()
        finally:
            cur.close()
            dbcon.close()
        if dbload:
            for t, s in dbload:
                bot.memory['karma'][t] = s


@priority('low')
@rule('[^!]*(\+\+|--)$')
def karmaRule(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    if trigger.sender[0] != '#':
        return
    if util.ignore_nick(bot, trigger.nick, trigger.host):
        return
    obj = trigger.raw.strip()
    if not obj or len(obj) < 3:
        return
    shortobj = obj[:-2].lower().strip()

    # Don't let users karma themselves
    if shortobj.lower() == trigger.nick.lower().strip('_`'):
        return

    karmee = nicks.NickPlus(trigger.nick, trigger.host)
    time_now = time.time()

    with bot.memory['karma_lock']:
        # TODO admin perks
        newkarm = None
        if not trigger.owner and karmee in bot.memory['karma_time'] and \
                time_now < bot.memory['karma_time'][karmee][0] + bot.memory['karma_time'][karmee][1]:
            # Optional: Increase the wait time a small amount for spamming
            '''
            bot.memory['karma_time'][karmee] = (
                bot.memory['karma_time'][karmee][0],
                int(bot.memory['karma_time'][karmee][1] * SMALL_WAIT_MULTIPLIER)
            )
            '''
            # PM the user to let them know their remaining time
            remaining = int(bot.memory['karma_time'][karmee][1] - (time_now - bot.memory['karma_time'][karmee][0]))
            bot.msg(trigger.nick,
                    'Your time has not ellapsed yet, so you may not use karma ' +
                    'for another %s seconds. ' % remaining +
                    'Please be considerate of others and keep spam to a minimum.')
            return

        # Update recorded last use and cooldown
        if trigger.owner:
            bot.memory['karma_time'][karmee] = (time_now, -1)
        else:
            bot.memory['karma_time'][karmee] = wait_time(bot, time_now, karmee)

        # Mod karma
        if obj.endswith("++"):
            newkarm = modkarma(bot, shortobj, 1)
        elif obj.endswith("--"):
            newkarm = modkarma(bot, shortobj, -1)

        bot.reply("Karma for %s is at %s [%is]" % (
            color(shortobj, fg='orange'),
            color(str(newkarm), fg='green'),
            bot.memory['karma_time'][karmee][1]))


def wait_time(bot, now, karmee):
    '''Takes time and nick, checks last wait time and returns next wait time for that nick'''
    _DEFAULT = 60
    _WAIT_MULTIPLIER = 1.75
    _WAIT_DIVISOR = 1.25
    _WAIT_SHORT_INTERVAL = 2.5
    _WAIT_LONG_INTERVAL = 10

    if karmee not in bot.memory['karma_time']:
        return (now, _DEFAULT)

    delta = now - bot.memory['karma_time'][karmee][0]

    if delta < 0:
        # Wut
        return (now, _DEFAULT)
    elif delta < bot.memory['karma_time'][karmee][1] * _WAIT_SHORT_INTERVAL:
        # User is using this often, increase wait time
        return (now, int(bot.memory['karma_time'][karmee][1] * _WAIT_MULTIPLIER))
    elif delta < bot.memory['karma_time'][karmee][1] * _WAIT_LONG_INTERVAL:
        # User is using slower, let's cut the time
        if bot.memory['karma_time'][karmee][1] / _WAIT_DIVISOR < _DEFAULT:
            return (now, _DEFAULT)
        else:
            return (now, int(bot.memory['karma_time'][karmee][1] / _WAIT_DIVISOR))
    else:
        return (now, _DEFAULT)


@commands('karma')
@example('!karma fzoo')
def karma(bot, trigger):
    '''Allows for voting on anything. ++ to upvote, -- to downvote. Reply will have a cool-down
    time in square brackets at the end. To check karma value, use !karma'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    obj = trigger.raw[7:].lower().strip()
    if not obj:
        return
    karm = modkarma(bot, obj, 0)
    bot.reply("Karma for %s is at %s" % (
        color(obj, fg='orange'),
        color(str(karm), fg='green')))


def modkarma(bot, obj, amount):
    dbcon = bot.db.connect()  # sqlite3 connection
    cur = dbcon.cursor()

    try:
        if obj in bot.memory['karma']:
            bot.memory['karma'][obj] += amount
            cur.execute('''UPDATE karma set score = ?
                        where tag = ?''',
                        (bot.memory['karma'][obj], obj))
        else:
            bot.memory['karma'][obj] = amount
            cur.execute('''INSERT into karma (tag, score)
                            VALUES (?, ?)''',
                        (obj, bot.memory['karma'][obj]))
        dbcon.commit()
        return bot.memory['karma'][obj]
    finally:
        cur.close()
        dbcon.close()


_link_page = Template('''
<!DOCTYPE html>
<html>
    <meta charset="UTF-8">
    <head><title>Karma Data Download</title></head>
    <p>The karma data is exported in three formats as seen below. Save the format you'd like and have a ball</p>
    <p>
        <a href="${json_path}" download>JSON format</a><br>
        <a href="${csv_path}" download>CSV format</a><br>
        <a href="${plain_path}" download>Plain text</a><br>
    </p>
</html>
''')


@commands('karma_export')
@rate('1000')
def karma_export(bot, trigger):
    '''Exports the karma database to a few common file formats.'''
    if not bot.memory['karma_export_dir']:
        bot.reply('This option is not configured.')
        return

    JSON_FILE = os.path.join(bot.memory['karma_export_dir'], 'karma.json')
    PLAIN_FILE = os.path.join(bot.memory['karma_export_dir'], 'karma.txt')
    CSV_FILE = os.path.join(bot.memory['karma_export_dir'], 'karma.csv')
    LINK_FILE = os.path.join(bot.memory['karma_export_dir'], 'karma.html')

    JSON_URL = os.path.join(bot.memory['karma_url'], 'karma.json')
    PLAIN_URL = os.path.join(bot.memory['karma_url'], 'karma.txt')
    CSV_URL = os.path.join(bot.memory['karma_url'], 'karma.csv')
    LINK_URL = os.path.join(bot.memory['karma_url'], 'karma.html')

    bot.reply('Exporting data, please wait...')

    with bot.memory['karma_lock']:
        try:
            with open(JSON_FILE) as f:
                previous_json = ''.join(f.readlines())
        except IOError:
            previous_json = ''
            bot.debug(__file__, log.format('IO error grabbing karma.json file contents. File may not exist yet'), 'warning')

        json_dump = json.dumps(bot.memory['karma'])

        # noclobber once. Don't really need to check every file
        if previous_json != json_dump:
            try:
                with open(JSON_FILE, 'w') as f:
                    bot.debug(__file__, log.format('Writing json'), 'verbose')
                    f.write(json_dump)

                plain_dump = '\n'.join(['%s %s' % (bot.memory['karma'][i], i) for i in bot.memory['karma']])
                print(pprint(plain_dump))
                with open(PLAIN_FILE, 'w') as f:
                    bot.debug(__file__, log.format('Writing plain file'), 'verbose')
                    f.write(plain_dump.encode('utf-8', 'replace'))

                with open(CSV_FILE, 'wb') as f:
                    bot.debug(__file__, log.format('Writing csv file'), 'verbose')
                    writer = csv.writer(f)
                    writer.writerows([(bot.memory['karma'][i], i.encode('utf-8', 'replace')) for i in bot.memory['karma']])

                link_page = _link_page.substitute(
                    json_path=JSON_URL,
                    csv_path=CSV_URL,
                    plain_path=PLAIN_URL)
                try:
                    with open(LINK_FILE) as f:
                        bot.debug(__file__, log.format('Reading link file'), 'verbose')
                        previous_links = ''.join(f.readlines())
                except IOError:
                    previous_links = ''
                    bot.debug(__file__, log.format('IO error grabbing karma.html file contents. File may not exist yet'), 'warning')
                if previous_links != link_page:
                    with open(LINK_FILE, 'w') as f:
                        bot.debug(__file__, log.format('writing link file'), 'verbose')
                        f.write(link_page)
            except IOError:
                bot.debug(__file__, log.format('IO error. check file permissions for karma export output.'), 'warning')
                return

            # wait 60s for web server to update
            time.sleep(60)
    bot.reply('The karma data has been exported to %s' % LINK_URL)


if __name__ == "__main__":
    print(__doc__.strip())
