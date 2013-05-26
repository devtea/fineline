"""
prompt.py - A Willie module that generates simple drawing ideas
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random, bisect

random.seed()

def setup(Willie):
    #Load from database when module is first loaded to reduce load over
    #each call

    #Load list of names
    global ponies
    ponies = []
    for row in Willie.db.prompt_ponies.keys():
        """Willie.debug("prompt.py", Willie.db.prompt_ponies.get(row[0],
            ('name','weight')), "verbose")"""
        ponies.append(Willie.db.prompt_ponies.get(row[0], ('name','weight')))
    Willie.debug("prompt.py", "Loaded " + str(len(ponies)) +
            " weighted ponies.", "verbose")

    #Load list of nouns
    global nouns
    nouns = []
    for row in Willie.db.prompt_nouns.keys():
        """Willie.debug("prompt.py", Willie.db.prompt_ponies.get(row[0],
            ('name','weight')), "verbose")"""
        nouns.append(Willie.db.prompt_nouns.get(row[0], 'noun'))
    Willie.debug("prompt.py", "Loaded " + str(len(nouns)) +
            " nouns.", "verbose")

    #Load list of verbs
    global verbs
    verbs = []
    for row in Willie.db.prompt_verbs.keys():
        """Willie.debug("prompt.py", Willie.db.prompt_ponies.get(row[0],
            ('name','weight')), "verbose")"""
        verbs.append(Willie.db.prompt_verbs.get(row[0], 'verb'))
    Willie.debug("prompt.py", "Loaded " + str(len(verbs)) +
            " verbs.", "verbose")



def weighted_choice(weighted):
    """Returns a random index from a list of tuples that contain
    (something, weight) where weight is the weighted probablity that
    that item should be chosen. Higher weights are chosen more often"""

    sum = 0
    sum_steps = []
    for item in weighted:
        sum = sum + int(item[1])
        sum_steps.append(sum)
    return bisect.bisect_right( sum_steps, random.uniform(0,sum))



def prompt(Willie, trigger):
    """Gives a short drawing prompt using ponies from the show."""

    Willie.debug("prompt.py", "==============", "verbose")
    Willie.debug("prompt.py", "Module started", "verbose")

    #Make our random selections for our prompt construction
    index_no = weighted_choice(ponies)
    sentence = ["Your random prompt is: ",
            ponies[index_no][0],
            random.choice(verbs).strip(),
            random.choice(nouns).strip() + "."]

    Willie.reply(" ".join(sentence))
#Match a command sequence eg !cmd
prompt.commands = ['prompt']

#Priorities of 'high', 'medium', and 'low' work
prompt.priority = 'medium'

#Willie is multithreaded by default.
#prompt.thread = False

#Limit in seconds of users ability to trigger module
prompt.rate = 35



if __name__ == "__main__":
    print __doc__.strip()
