"""
episodes.py - A simple Willie module to return and modify TV episodes
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import random
import re

from willie.module import commands, example

global episodes
episodes = {}

random.seed()


def setup(Willie):
    reload(Willie)


def reload(Willie):
    global episodes
    episodes = {}
    cnt = 0  # for debug
    for row in Willie.db.episodes.keys("season, episode"):
        s, e, t = Willie.db.episodes.get(
            row,
            ('season', 'episode', 'title'),
            ("season", "episode")
        )
        if s not in episodes:
            episodes[s] = {}
            #Willie.debug('episodes.py', 'added season %i' % s, 'verbose')
        if e not in episodes[s]:
            episodes[s][e] = t
            #Willie.debug('episodes.py', 'added episode %i' % e, 'verbose')
            cnt = cnt + 1  # for debug
        else:
            Willie.debug(u'episodes.py',
                         u'Warning: Duplicate episode found!',
                         u'warning'
                         )
    #Willie.debug(u"episodes.py", u"Loaded %i eps." % cnt, u"verbose")


def get_ep(se):
    """Accepts a list containing season and episode"""
    if len(se) == 2 and se[0] in episodes and se[1] in episodes[se[0]]:
            title = episodes[se[0]][se[1]]
            return u"The episode is season %i, episode %i, %s." % (
                se[0], se[1], title)
    return u"I can't seem to find that episode."


@commands('reload_eps')
def reload_eps(Willie, trigger):
    """ADMIN: Reloads cached episodes from the database."""
    Willie.debug(u"episodes.py:reload_eps", u"Triggered", u"verbose")
    if trigger.admin:
        Willie.say(u"Reloading episodes.")
        reload(Willie)
        Willie.say(u"Done.")
    else:
        Willie.debug(u"episodes.py",
                     u"%s just tried to reload episodes..." % trigger.nick,
                     u"always"
                     )


@commands('add_ep')
@example('!add_ep S00E00 This is not a title')
def add_ep(Willie, trigger):
    """ADMIN: Adds an episode to the database. Admin only"""
    Willie.debug(u"episodes.py:add_ep", u"Triggered", u"verbose")
    if trigger.admin:
        # assume input is SxxExx title~~~~~~
        # eg ['!test', 'S01E01', 'Title', ...]
        command = trigger.args[1].split()
        if len(command) > 2:
            #Test the second argument for sanity, eg 'S01E03'
            if re.match(r'^S\d{1,2}E\d{1,2}$',
                        command[1],
                        flags=re.IGNORECASE
                        ):
                Willie.debug("episodes.py:episode", "Ep is sane", "verbose")
                season, __, ep = trigger.args[1].split()[1].upper().partition(
                    u"E"
                )
                season = int(season.lstrip("S"))
                ep = int(ep)
                title = u' '.join(i for i in command if command.index(i) > 1)
                Willie.debug(u'episodes.py',
                             u'Season %i, episode %i' % (season, ep),
                             u'verbose'
                             )
                message = get_ep([season, ep])
                if message.startswith('T'):
                    Willie.reply("That episode already exists!")
                    Willie.reply(message)
                else:
                    Willie.db.episodes.update(
                        [season, ep],  # values
                        {'season': season,
                         'episode': ep,
                         'title': title
                         },  # new vals
                        ("season", "episode")  # Keys
                    )
                    reload(Willie)  # Ineffecient, but easy...
                    Willie.reply("Successfully added!")
            else:
                Willie.debug("episodes.py:episode",
                             "Argument is insane",
                             "verbose"
                             )
                Willie.reply("I don't understand that.")
        else:
            Willie.debug("episodes.py:episode", "Not enough args", "verbose")
            Willie.reply("Uh, what episode?")
    else:
        Willie.debug("episodes.py",
                     "%s just tried to add an episode..." % trigger.nick,
                     "always"
                     )


@commands('episode', 'ep')
@example('!episode S02E11')
def episode(Willie, trigger):
    """Returns a specified episode by season and episode."""
    Willie.debug("episodes.py:episode", "Triggered", "verbose")
    #test the arguments returned, e.g. ['.episode', 'S01E03']
    if len(trigger.args[1].split()) == 2:
        #Test the second argument for sanity, eg 'S01E03'
        if re.match(r'^S\d{1,2}E\d{1,2}$',
                    trigger.args[1].split()[1],
                    flags=re.IGNORECASE
                    ):
            Willie.debug("episodes.py:episode",
                         "Argument is sane",
                         "verbose"
                         )
            season, __, ep = trigger.args[1].split()[1].upper().partition("E")
            Willie.reply(get_ep([int(season.lstrip("S")), int(ep)]))
        else:
            Willie.debug("episodes.py:episode",
                         "Argument is insane",
                         "verbose"
                         )
            Willie.reply(("I don't understand that. Try '%s: help " +
                         "episode'") % Willie.nick)
    elif len(trigger.args[1].split()) > 2:
        Willie.debug("episodes.py:episode", "too many args", "verbose")
        Willie.reply("I don't understand that. Try '%s: help " +
                     "episode'" % Willie.nick)
    else:
        Willie.debug("episodes.py:episode", "Not enough args", "verbose")
        randep(Willie, trigger)


@commands('randep', 'rep', 'randomep')
def randep(Willie, trigger):
    """Returns a random episode."""
    Willie.debug("episodes.py:randep", "Triggered", "verbose")
    season = random.randint(1, len(episodes))
    episode = random.randint(1, len(episodes[season]))
    Willie.reply(get_ep([season, episode]))


if __name__ == "__main__":
    print __doc__.strip()
