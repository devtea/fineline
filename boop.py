"""
boop.py - A Willie module that does something
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
# TODO user aliases
from __future__ import print_function

import os.path
from willie.module import commands, example
from willie.tools import Nick
import random
import threading
import traceback

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
    import colors
except:
    import imp
    import sys
    try:
        print("trying manual import of colors")
        fp, pathname, description = imp.find_module('colors', [os.path.join('.', '.willie', 'modules')])
        colors = imp.load_source('colors', pathname, fp)
        sys.modules['colors'] = colors
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


_excludes = []
_listexclude = ['sex', 'fucking', 'life', 'death', 'money', 'all', 'everything']
_front = ['any', 'some']
_back = ['one', 'body', 'pony', 'poni', 'pone']
_anyone = [a + b for a in _front for b in _back]
_everyone = ['every' + b for b in _back]
_defaults = [('boop', u'boops %s'),
             ('all', u'Yells "BOOP" and giggles to herself'),
             ('self', u'looks funny as she crosses her eyes and tries to boop herself')]


def setup(bot):
    if 'boop' not in bot.memory:
        bot.memory['boop'] = {}
    if 'lock' not in bot.memory['boop']:
        bot.memory['boop']['lock'] = threading.Lock()

    with bot.memory['boop']['lock']:
        bot.memory['boop']['lists'] = {}
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        dblists = None
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS boop_lists
                           (list TEXT, nick TEXT, host TEXT)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS boops
                           (style TEXT NOT NULL, boop TEXT NOT NULL UNIQUE)''')
            dbcon.commit()

            if not bot.memory['boop']['lists']:
                cur.execute('select list, nick, host from boop_lists')
                dblists = cur.fetchall()
            if 'boop' not in bot.memory['boop']:
                cur.execute('SELECT style, boop from boops')
                dbboops = cur.fetchall()
                if dbboops:
                    boops = dbboops
                else:
                    boops = _defaults
                    for s, b in boops:
                        cur.execute('''INSERT INTO boops (style, boop)
                                    VALUES (?, ?)''', (s, b))
                        dbcon.commit()

                for s, b in boops:
                    # This will set up three lists, 'boop', 'self', and 'all'
                    if s not in bot.memory['boop']:
                        bot.memory['boop'][s] = []
                    bot.memory['boop'][s].append(b)
        finally:
            cur.close()
            dbcon.close()

        for l, n, h in dblists:
            if l not in bot.memory['boop']['lists']:
                bot.memory['boop']['lists'][l] = []
            bot.memory['boop']['lists'][l].append(nicks.NickPlus(n, h))


@commands(u'boop-add')
@example(u'!boop-add self boops herself!')
def boop_add(bot, trigger):
    '''ADMIN: Adds boops. First argument should be one of 'self', 'boop', or 'all' '''
    if not trigger.owner:
        return
    try:
        arguments = trigger.args[1].split()[1:]
    except IndexError:
        # Nothing provided
        return
    if len(arguments) < 2 or arguments[0] not in ('self', 'boop', 'all'):
        bot.reply("malformed arguments")
        return
    if arguments[0] == 'boop' and '%s' not in arguments:
        bot.reply("You must supply exactly one string substitution (%s) for the boop")
        return

    boop = u' '.join(arguments[1:])
    if boop not in bot.memory['boop'][arguments[0]]:
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            cur.execute('''INSERT INTO boops (style, boop)
                        VALUES (?, ?)''', (arguments[0], boop))
            dbcon.commit()
            bot.memory['boop'][arguments[0]].append(boop)
        except:
            bot.debug(__file__, log.format(u'ERROR: Unable to insert boop'), u'always')
            print(traceback.format_exc())
            bot.reply('Error inserting!')
        else:
            bot.reply('Added.')
        finally:
            cur.close()
            dbcon.close()
    else:
        bot.reply('That already exists.')


@commands(u'boop-del')
@example(u'!boop-del self boops %s')
def boop_del(bot, trigger):
    '''ADMIN: attempts to delete boops. First argument should be one of 'self', 'boop', or 'all' '''
    if not trigger.owner:
        return
    try:
        arguments = trigger.args[1].split()[1:]
    except IndexError:
        # Nothing provided
        return
    if len(arguments) < 2 or arguments[0] not in ('self', 'boop', 'all'):
        bot.reply("malformed arguments")
        return
    boop = u' '.join(arguments[1:])

    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    try:
        cur.execute("""SELECT COUNT(*)
                       FROM boops
                       WHERE style = ?
                       AND boop like ?""", (arguments[0], boop))
        count = cur.fetchone()[0]
        cur.execute("""DELETE FROM boops
                       WHERE style = ?
                       AND boop like ?""", (arguments[0], boop))
        dbcon.commit()
    except:
        bot.debug(__file__, log.format(u'ERROR: error removing boop'), u'always')
        print(traceback.format_exc())
        bot.reply("Error removing boops, probably malformed text provided for the like '?' portion of the SQL query.")
    else:
        bot.reply('%s boop(s) removed.' % count)


@commands(u'boop')
def boop(bot, trigger):
    """Boops, what else?"""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    try:
        target = nicks.NickPlus(trigger.args[1].split()[1])
    except IndexError:
        bot.action(random.choice(bot.memory['boop']['boop']) % trigger.nick)
    else:
        if target == trigger.nick or target.lower() in ['me', 'myself']:
            bot.action(random.choice(bot.memory['boop']['boop']) % trigger.nick)
        elif target == bot.nick or target.lower() in ['yourself', 'you']:
            bot.action(random.choice(bot.memory['boop']['self']))
        elif target.lower() in _everyone:
            bot.action(random.choice(bot.memory['boop']['all']))
        elif target.lower() in _anyone:
            target = bot.nick
            nick_list = []
            nick_list.extend(nicks.in_chan(bot, trigger.sender))
            while target == bot.nick:
                target = random.choice(nick_list)
            bot.action(random.choice(bot.memory['boop']['boop']) % target)
        elif target in _excludes:
            bot.say(u"I'm not doing that.")
        elif nicks.in_chan(bot, trigger.sender, target):
            nick_list = []
            nick_list.extend(nicks.in_chan(bot, trigger.sender))
            i = nicks.in_chan(bot, trigger.sender).index(target)
            target = nick_list.pop(i)
            # TODO small chance to boop random person
            bot.action(random.choice(bot.memory['boop']['boop']) % target)
        elif target.lower() in bot.memory['boop']['lists'] and len(bot.memory['boop']['lists'][target.lower()]) > 0:
            message = u' '.join(trigger.args[1].split()[2:])
            msg = 'boops'
            nick_list = []
            nick_list.extend(nicks.in_chan(bot, trigger.sender))
            for name in bot.memory['boop']['lists'][target.lower()]:
                if nicks.in_chan(bot, trigger.sender, name):
                    try:
                        i = nick_list.index(name)
                        name = nick_list.pop(i)
                        msg = "%s %s," % (msg, name)
                    except ValueError:
                        # One person may have multiple nicks in list but only
                        # one in room. Value errors will be thrown after the
                        # first nick matches and is popped from the list.
                        pass
            msg = msg.strip(',')
            if msg != 'boops':
                msg = "%s %s" % (msg, '[%s]' % colors.colorize(target.lower(), [u'orange']))

                # TODO account for really long messages
                if message:
                    msg = "%s %s" % (msg, '| <%s> %s')
                    bot.action(msg % (colors.colorize(trigger.nick, [u'purple']),
                                      colors.colorize(message, [u'green'])
                                      ))
                else:
                    bot.action(msg)
            else:
                bot.reply("Sorry, I don't see anyone from that list here right now.")
        else:
            bot.reply(u'Sorry, I don\'t see %s around here.' % target)


@commands(u'optin')
def optin(bot, trigger):
    """Opt into being pinged/booped for a list."""
    if len(trigger.args[1].split()) > 2:
        bot.reply('List names cannot contain spaces.')
        return
    with bot.memory['boop']['lock']:
        # Database stuff
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            # multiword triggers cause problems.
            # target = trigger.args[1].split(' ', 1)[1].lower()
            target = trigger.args[1].split()[1].lower()
        except IndexError:
            bot.reply("You must specify a list to opt into.")
        else:
            name = nicks.NickPlus(trigger.nick, trigger.host)
            if target in _listexclude:
                bot.reply(u'You can\'t opt into that...')
                return
            elif target in bot.memory['boop']['lists']:
                if Nick(trigger.nick) not in bot.memory['boop']['lists'][target]:
                    bot.memory['boop']['lists'][target].append(name)
                    cur.execute('''insert into boop_lists (list, nick, host)
                                values (?, ?, ?)''', (target, trigger.nick, trigger.host))
                    dbcon.commit()
                bot.reply('You are on the %s list.' % colors.colorize(target, [u'orange']))
            else:
                bot.memory['boop']['lists'][target] = [nicks.NickPlus(trigger.nick)]
                cur.execute('''insert into boop_lists (list, nick, host)
                               values (?, ?, ?)''', (target, trigger.nick, trigger.host))
                dbcon.commit()
                bot.reply('You are on the %s list.' % colors.colorize(target, [u'orange']))
        finally:
            cur.close()
            dbcon.close()


@commands(u'optout')
def optout(bot, trigger):
    """Opt out from being pinged/booped for a list."""
    if len(trigger.args[1].split()) > 2:
        bot.reply('List names cannot contain spaces.')
        return
    with bot.memory['boop']['lock']:
        # Database stuff
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            target = trigger.args[1].split()[1].lower()
        except IndexError:
            bot.reply("You must specify a list to opt out of.")
        else:
            name = nicks.NickPlus(trigger.nick, trigger.host)
            if target in bot.memory['boop']['lists'] and name in bot.memory['boop']['lists'][target]:
                bot.memory['boop']['lists'][target] = [i for i in bot.memory['boop']['lists'][target] if i != name]
                cur.execute('''delete from boop_lists
                               where lower(list) = ?
                               and (lower(nick) = ?
                                   or lower(host) = ?
                                   )
                               ''', (target, trigger.nick.lower(), trigger.host.lower()))
                dbcon.commit()
                bot.reply('You have been removed from the %s list.' % colors.colorize(target, [u'orange']))
            elif target in ['all', 'everything']:
                for i in bot.memory['boop']['lists']:
                    try:
                        bot.memory['boop']['lists'][i].remove(name)
                    except:
                        pass
                cur.execute('''delete from boop_lists
                               where lower(nick) = ?
                               or lower(host) = ?
                               ''', (trigger.nick.lower(), trigger.host.lower()))
                dbcon.commit()
                bot.reply('You have been removed from the all lists.')
            elif target in bot.memory['boop']['lists']:
                bot.reply('You are not on that list.')
            else:
                bot.reply('That list does not exist.')
        finally:
            cur.close()
            dbcon.close()


@commands(u'opts', u'opt')
def opts(bot, trigger):
    # TODO list opts lists
    pass


if __name__ == "__main__":
    print(__doc__.strip())
