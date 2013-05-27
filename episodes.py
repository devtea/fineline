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
    #load data from database
    global episodes
    episodes = []
    for row in Willie.db.episodes.keys("season, episode"):
        episodes.append(Willie.db.episodes.get(row,
            ('season','episode','title'), ("season", "episode")))
    Willie.debug("episodes.py", "Loaded " + str(len(episodes)) +
            " episodes.", "verbose")

def say_ep(Willie, trigger, episode):
    """Accepts a list optionally containing an int of the index of the ep"""
    if len(episode) == 0:
        Willie.debug("episodes.py:episode", "Episode not found",
                "verbose")
        Willie.reply("I can't seem to find that episode.")
    else:
        episode = episodes[episode[0]]
        Willie.debug("episodes.py:episode", episode, "verbose")

        sentence = ["The episode is Season", str(episode[0]) + ",",
            "Episode", str(episode[1]) + ",", episode[2] + "." ]
        Willie.reply(" ".join(sentence))

def reload_eps(Willie, trigger):
    """Reloads cached episodes from the database. Admin only."""
    Willie.debug("episodes.py:reload_eps", "Triggered", "verbose")
    if trigger.admin:
        Willie.say("Reloading episodes.")

        #load data from database
        global episodes
        episodes = []
        for row in Willie.db.episodes.keys("season, episode"):
            episodes.append(Willie.db.episodes.get(row,
                ('season','episode','title'), ("season", "episode")))
        Willie.debug("episodes.py", "Loaded " + str(len(episodes)) +
                " episodes.", "verbose")
        Willie.say("Done. Loaded " + str(len(episodes)) + " episodes.")
        Willie.debug("episodes.py", episodes, "verbose")
    else:
        Willie.debug("episodes.py", trigger.nick +
                " just tried to reload episodes...", "always")
reload_eps.commands = ['reload_eps']
reload_eps.priority = 'medium'
reload_eps.example = ".reload_eps"

def add_ep(Willie, trigger):
    """Adds an episode to the database. Admin only"""
    Willie.debug("episodes.py:add_ep", "Triggered", "verbose")
    if trigger.admin:
        Willie.debug("episodes.py", "This module is unfinished", "warning")
        Willie.reply("Hey knucklehead, you never finished this module!")
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
        if re.match(r'^S\d\dE\d\d$', trigger.args[1].split()[1],
                flags=re.IGNORECASE):
            Willie.debug("episodes.py:episode", "Argument is sane",
                "verbose")
            season, __, ep = trigger.args[1].split()[1].upper().partition("E")
            index = (int(season.lstrip("S")), int(ep))
            Willie.debug("episodes.py:episode", index, "verbose")
            #get a table with the index number of the episode or null
            index_no = [i for i, t in enumerate(episodes)
                    if (t[0], t[1]) == index]
            say_ep(Willie, trigger, index_no)
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
episode.priority = 'medium'
episode.rate = 35
episode.example = ".episode S02E11"

def randep(Willie, trigger):
    """Returns a random episode."""
    Willie.debug("episodes.py:randep", "Triggered", "verbose")
    say_ep(Willie, trigger, [random.randint(0,len(episodes)-1)] )
randep.commands = ['randep', 'rep', 'randomep']
randep.priority = 'medium'
randep.rate = 35
randep.example = ".randep"

if __name__ == "__main__":
    print __doc__.strip()
