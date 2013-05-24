"""
prompt.py - A simple Willie module prompt
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random, bisect


    #index_no = weighted_choice(ponies)
def weighted_choice(weighted):
    sum = 0
    sum_steps = []

    for item in weighted:
        sum = sum + int(item[1])
        sum_steps.append(sum)

    return bisect.bisect_right( sum_steps, random.uniform(0,sum))


def prompt(Willie, trigger):
    """Gives a short drawing prompt using ponies from the show."""
    #think about hitting the DB once during a setup function

    Willie.debug("prompt.py", "==============", "verbose")
    Willie.debug("prompt.py", "Module started", "verbose")

    Willie.reply("Okay, your random prompt is as follows:")

    #Debugging messages showing the size of the tables
    Willie.debug("prompt.py", "Ponies: " + str(Willie.db.prompt_ponies.size()),
            "verbose")
    Willie.debug("prompt.py", "Nouns: " + str(Willie.db.prompt_nouns.size()),
            "verbose")
    Willie.debug("prompt.py", "Verbs: " + str(Willie.db.prompt_verbs.size()),
            "verbose")


    #Load list of ponies
    ponies = []
    for row in Willie.db.prompt_ponies.keys():
        """Willie.debug("prompt.py", Willie.db.prompt_ponies.get(row[0],
            ('name','weight')), "verbose")"""
        ponies.append(Willie.db.prompt_ponies.get(row[0], ('name','weight')))
    Willie.debug("prompt.py", "Loaded " + str(len(ponies)) +
            " weighted ponies.", "verbose")

    #Load list of nouns
    nouns = []
    for row in Willie.db.prompt_nouns.keys():
        """Willie.debug("prompt.py", Willie.db.prompt_ponies.get(row[0],
            ('name','weight')), "verbose")"""
        nouns.append(Willie.db.prompt_nouns.get(row[0], 'noun'))
    Willie.debug("prompt.py", "Loaded " + str(len(nouns)) +
            " nouns.", "verbose")

    #Load list of verbs
    verbs = []
    for row in Willie.db.prompt_verbs.keys():
        """Willie.debug("prompt.py", Willie.db.prompt_ponies.get(row[0],
            ('name','weight')), "verbose")"""
        verbs.append(Willie.db.prompt_verbs.get(row[0], 'verb'))
    Willie.debug("prompt.py", "Loaded " + str(len(verbs)) +
            " verbs.", "verbose")

    #Make our random selections for our prompt construction
    #Willie.debug("prompt.py", random.choice(verbs), "verbose")
    index_no = weighted_choice(ponies)
    pony = ponies[index_no][0]
    verb = random.choice(verbs).strip()
    noun = random.choice(nouns).strip()

    Willie.reply(pony + " " + verb + " " + noun + ".")


### COMMAND
#Match a command sequence eg !cmd
prompt.commands = ['prompt']

#Priorities of 'high', 'medium', and 'low' work
prompt.priority = 'medium'

#Willie is multithreaded by default.
#prompt.thread = False

#Limit in seconds of users ability to trigger module
prompt.rate = 30

#Example used in help query to bot for commands
prompt.example = ".prompt"

if __name__ == "__main__":
    print __doc__.strip()
