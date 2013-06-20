"""
episodes.py - A simple Willie module to return and modify TV episodes
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import re

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
                ('season','episode','title'),
                ("season", "episode")
                )
        if s not in episodes:
            episodes[s] = {}
            Willie.debug('episodes.py', 'added season %i' % s, 'verbose')
        if e not in episodes[s]:
            episodes[s][e] = t
            Willie.debug('episodes.py', 'added episode %i' % e, 'verbose')
            cnt = cnt + 1  # for debug
        else:
            Willie.debug('episodes.py', 'Warning: Duplicate episode found!', 'warning')

    Willie.debug("episodes.py", "Loaded %i eps." % cnt, "verbose")


def get_ep(se):
    """Accepts a list containing season and episode"""
    if len(se) == 2 and se[0] in episodes and se[1] in episodes[se[0]]:
            title = episodes[se[0]][se[1]]
            return "The episode is season %i, episode %i, %s." % (
                se[0], se[1], title)
    return "I can't seem to find that episode."


def reload_eps(Willie, trigger):
    """ADMIN: Reloads cached episodes from the database."""
    Willie.debug("episodes.py:reload_eps", "Triggered", "verbose")
    if trigger.admin:
        Willie.say("Reloading episodes.")
        reload(Willie)
        Willie.say("Done.")
    else:
        Willie.debug("episodes.py", trigger.nick +
                " just tried to reload episodes...", "always")
reload_eps.commands = ['reload_eps']
reload_eps.example = ".reload_eps"


# TODO
def add_ep(Willie, trigger):
    """ADMIN: Adds an episode to the database. Admin only"""
    Willie.debug("episodes.py:add_ep", "Triggered", "verbose")
    if trigger.admin:
        # assume input is SxxExx title~~~~~~
        command = trigger.args[1].split()  # eg ['!test', 'S01E01', 'Title', ...]
        if len(command) > 2:
            #Test the second argument for sanity, eg 'S01E03'
            if re.match(r'^S\d{1,2}E\d{1,2}$', command[1], flags=re.IGNORECASE):
                Willie.debug("episodes.py:episode", "Ep is sane", "verbose")
                season, __, ep = trigger.args[1].split()[1].upper().partition("E")
                season = int(season.lstrip("S"))
                ep = int(ep)
                title = ' '.join(i for i in command if command.index(i) > 1)
                Willie.debug('', 'Season %i, episode %i' % (season, ep), 'verbose')
                message = get_ep([season, ep])
                if message.startswith('T'):
                    Willie.reply("That episode already exists!")
                    Willie.reply(message)
                else:
                    Willie.db.episodes.update(
                            [season, ep],  #values
                            {'season': season, 'episode': ep, 'title': title},  #new vals
                            ("season", "episode")  #Keys
                            )
                    reload(Willie)  # Ineffecient, but easy...
                    Willie.reply("Successfully added!")
            else:
                Willie.debug("episodes.py:episode", "Argument is insane",
                        "verbose")
                Willie.reply("I don't understand that.")
        else:
            Willie.debug("episodes.py:episode", "Not enough args", "verbose")
            randep(Willie, trigger)
    else:
        Willie.debug("episodes.py", trigger.nick +
                " just tried to add an episode...", "always")
add_ep.commands = ['add_ep']
add_ep.priority = 'medium'
add_ep.example = ".add_ep"


def episode(Willie, trigger):
    """Returns a specified episode by season and episode."""
    Willie.debug("episodes.py:episode", "Triggered", "verbose")
    #test the arguments returned, e.g. ['.episode', 'S01E03']
    if len(trigger.args[1].split()) == 2:
        #Test the second argument for sanity, eg 'S01E03'
        if re.match(r'^S\d{1,2}E\d{1,2}$', trigger.args[1].split()[1],
                flags=re.IGNORECASE):
            Willie.debug("episodes.py:episode", "Argument is sane",
                "verbose")
            season, __, ep = trigger.args[1].split()[1].upper().partition("E")
            Willie.reply(get_ep([int(season.lstrip("S")), int(ep)]))
        else:
            Willie.debug("episodes.py:episode", "Argument is insane",
                    "verbose")
            Willie.reply("I don't understand that. Try '" + Willie.nick +
                    ": help episode'")
    elif len(trigger.args[1].split()) > 2:
        Willie.debug("episodes.py:episode", "too many args", "verbose")
        Willie.reply("I don't understand that. Try '" + Willie.nick +
                ": help episode'")
    else:
        Willie.debug("episodes.py:episode", "Not enough args", "verbose")
        randep(Willie, trigger)
episode.commands = ['episode', 'ep']
episode.rate = 35
episode.example = ".episode S02E11"


def randep(Willie, trigger):
    """Returns a random episode."""
    Willie.debug("episodes.py:randep", "Triggered", "verbose")
    season = random.randint(1,len(episodes))
    episode = random.randint(1,len(episodes[season]))
    Willie.reply(get_ep([season,episode]))
randep.commands = ['randep', 'rep', 'randomep']
randep.priority = 'medium'
randep.rate = 35
randep.example = ".randep"


if __name__ == "__main__":
    print __doc__.strip()
