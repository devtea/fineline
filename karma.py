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
from willie.tools import Nick

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


def setup(bot):
    if bot.config.has_section('karma') and bot.config.has_option('karma', 'export_dir'):
        bot.memory['karma_export_dir'] = bot.config.karma.export_dir
        bot.memory['karma_url'] = bot.config.karma.url
    else:
        bot.memory['karma_export_dir'] = None
    bot.memory
    if 'karma_lock' not in bot.memory:
        bot.memory['karma_lock'] = threading.Lock()
    if 'karma_time' not in bot.memory:
        bot.memory['karma_time'] = {}
    bot.memory['karma'] = {}

    with bot.memory['karma_lock']:
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
    obj = trigger.bytes.strip()
    if not obj or len(obj) < 3:
        return
    shortobj = obj[:-2].lower().strip()

    # don't let users karma themselves
    if shortobj.lower() == trigger.nick.lower().strip('_`'):
        return

    with bot.memory['karma_lock']:
        newkarm = None
        if timecheck(bot, trigger):
            if obj.endswith("++"):
                newkarm = modkarma(bot, shortobj, 1)
            elif obj.endswith("--"):
                newkarm = modkarma(bot, shortobj, -1)
            bot.reply("Karma for %s is at %i" % (shortobj, newkarm))
        else:
            bot.reply("You just used karma! You can't use it again for a bit.")


def timecheck(bot, trigger):
    if trigger.admin:
        return True
    if Nick(trigger.nick) in bot.memory['karma_time'] \
            and time.time() < bot.memory['karma_time'][Nick(trigger.nick)] + 60:
        return False
    bot.memory['karma_time'][Nick(trigger.nick)] = time.time()
    return True


@commands('karma')
@example('!karma fzoo')
def karma(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    obj = trigger.bytes[7:].lower().strip()
    if not obj:
        return
    karm = modkarma(bot, obj, 0)
    bot.reply("Karma for %s is at %i" % (obj, karm))


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
