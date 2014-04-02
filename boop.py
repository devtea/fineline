"""
boop.py - A Willie module that does something
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
# TODO user aliases
from __future__ import print_function

from willie.module import commands
from willie.tools import Nick
import random
import threading

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        print("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', ['./.willie/modules/'])
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
        fp, pathname, description = imp.find_module('colors', ['./.willie/modules/'])
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
        fp, pathname, description = imp.find_module('nicks', ['./.willie/modules/'])
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
_boop = [u'boops %s',
         u'boops %s http://i.imgur.com/ruiIBf5.gif',
         u'boops %s http://i.imgur.com/QlSFlMK.gif',
         u'boops %s http://i.imgur.com/nra4yDL.gif',
         u'boops %s http://i.imgur.com/I8wxiat.jpg',
         u'boops %s http://i.imgur.com/ZQCHJTM.png',  # handsockz
         u'boops %s http://i.imgur.com/WhSWjJa.png',  # grenadder
         u'boops %s http://i.imgur.com/YryE7MX.png',  # brainstew00
         u'boops %s http://i.imgur.com/j94IXvg.gif',  # The4thaggie
         u'boops %s http://i.imgur.com/4B42aPA.png',  # bobdude0
         u'boops %s just a bit too hard http://i.imgur.com/Jz6jS.gif',
         u'boops %s... politely... http://i.imgur.com/nRwXn.gif',
         u'sneaks up and boops %s',
         u'licks her hoof and boops %s',
         u'boops %s on the nose',
         u'trips and accidentally boops %s in the eye',
         u'gently boops %s on the lips',
         u'"accidentally" boops %s on the plot...',
         u'boops %s before realizing she stepped in something smelly earlier...',
         u'giggles and boops %s',
         u'sticks her tongue out and boops %s',
         u'tries to boop %s, but... http://i.imgur.com/3mFn5YW.gif'
         ]
_self = [u'spins around in circles trying to boop herself http://i.imgur.com/igq9Mio.gif',
         u'looks funny as she crosses her eyes and tries to boop herself',
         u'pulls a mirror out of nowhere and boops her reflection'
         ]
_all = [u'yells "BOOP" and giggles to herself',
        u'runs around the room booping everyone'
        ]


def setup(bot):
    if 'boop_lock' not in bot.memory:
        bot.memory['boop_lock'] = threading.Lock()
    with bot.memory['boop_lock']:
        bot.memory['boop_lists'] = {}
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        dbnames = None
        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS boop_lists
                           (list text, nick text, host text)''')
            dbcon.commit()

            if not bot.memory['boop_lists']:
                cur.execute('select list, nick, host from boop_lists')
                dbnames = cur.fetchall()
        finally:
            cur.close()
            dbcon.close()
        for l, n, h in dbnames:
            if l not in bot.memory['boop_lists']:
                bot.memory['boop_lists'][l] = []
            bot.memory['boop_lists'][l].append(nicks.NickPlus(n, h))


@commands(u'boop')
def boop(bot, trigger):
    """Boops."""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    try:
        target = nicks.NickPlus(trigger.args[1].split()[1])
    except IndexError:
        bot.action(random.choice(_boop) % trigger.nick)
    else:
        if target == trigger.nick or target.lower() in ['me', 'myself']:
            bot.action(random.choice(_boop) % trigger.nick)
        elif target == bot.nick or target.lower() in ['yourself', 'you']:
            bot.action(random.choice(_self))
        elif target in _everyone:
            bot.action(random.choice(_all))
        elif target in _anyone:
            target = bot.nick
            nick_list = []
            nick_list.extend(nicks.in_chan(bot, trigger.sender))
            while target == bot.nick:
                target = random.choice(nick_list)
            bot.action(random.choice(_boop) % target)
        elif target in _excludes:
            bot.say(u"I'm not doing that.")
        elif nicks.in_chan(bot, trigger.sender, target):
            nick_list = []
            nick_list.extend(nicks.in_chan(bot, trigger.sender))
            i = nicks.in_chan(bot, trigger.sender).index(target)
            target = nick_list.pop(i)
            # TODO small chance to boop random person
            bot.action(random.choice(_boop) % target)
        elif target in bot.memory['boop_lists'] and len(bot.memory['boop_lists'][target]) > 0:
            message = u' '.join(trigger.args[1].split()[2:])
            msg = 'boops'
            nick_list = []
            nick_list.extend(nicks.in_chan(bot, trigger.sender))
            for name in bot.memory['boop_lists'][target]:
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
            msg = "%s %s" % (msg, '[%s]' % colors.colorize(target, [u'orange']))

            # TODO account for really long messages
            if message:
                msg = "%s %s" % (msg, '| <%s> %s')
                bot.action(msg % (colors.colorize(trigger.nick, [u'purple']),
                                  colors.colorize(message, [u'blue'])
                                  ))
            else:
                bot.action(msg)
        else:
            bot.reply(u'Sorry, I don\'t see %s around here.' % target)


@commands(u'optin')
def optin(bot, trigger):
    """Opt into being pinged/booped for a list."""
    if len(trigger.args[1].split()) > 2:
        bot.reply('List names cannot contain spaces.')
        return
    with bot.memory['boop_lock']:
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
            elif target in bot.memory['boop_lists']:
                if Nick(trigger.nick) not in bot.memory['boop_lists'][target]:
                    bot.memory['boop_lists'][target].append(name)
                    cur.execute('''insert into boop_lists (list, nick, host)
                                values (?, ?, ?)''', (target, trigger.nick, trigger.host))
                    dbcon.commit()
                bot.reply('You are on the %s list.' % colors.colorize(target, [u'orange']))
            else:
                bot.memory['boop_lists'][target] = [nicks.NickPlus(trigger.nick)]
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
    with bot.memory['boop_lock']:
        # Database stuff
        dbcon = bot.db.connect()
        cur = dbcon.cursor()
        try:
            target = trigger.args[1].split()[1].lower()
        except IndexError:
            bot.reply("You must specify a list to opt out of.")
        else:
            name = nicks.NickPlus(trigger.nick, trigger.host)
            if target in bot.memory['boop_lists'] and name in bot.memory['boop_lists'][target]:
                bot.memory['boop_lists'][target] = [i for i in bot.memory['boop_lists'][target] if i != name]
                cur.execute('''delete from boop_lists
                               where lower(list) = ?
                               and (lower(nick) = ?
                                   or lower(host) = ?
                                   )
                               ''', (target, trigger.nick.lower(), trigger.host.lower()))
                dbcon.commit()
                bot.reply('You have been removed from the %s list.' % colors.colorize(target, [u'orange']))
            elif target in ['all', 'everything']:
                for i in bot.memory['boop_lists']:
                    try:
                        bot.memory['boop_lists'][i].remove(name)
                    except:
                        pass
                cur.execute('''delete from boop_lists
                               where lower(nick) = ?
                               or lower(host) = ?
                               ''', (trigger.nick.lower(), trigger.host.lower()))
                dbcon.commit()
                bot.reply('You have been removed from the all lists.')
            elif target in bot.memory['boop_lists']:
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
