"""
prompt.py - A Willie module that generates simple drawing ideas
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import random
import bisect

from willie.module import commands

random.seed()


def setup(Willie):
    #Load list of names
    global ponies
    ponies = []
    for row in Willie.db.prompt_ponies.keys():
        ponies.append(Willie.db.prompt_ponies.get(row[0], ('name', 'weight')))
    Willie.debug(u"prompt.py",
                 u"Loaded %s weighted ponies." % str(len(ponies)),
                 u"verbose"
                 )
    #Load list of nouns
    global nouns
    nouns = []
    for row in Willie.db.prompt_nouns.keys():
        nouns.append(Willie.db.prompt_nouns.get(row[0], 'noun'))
    Willie.debug(u"prompt.py",
                 u"Loaded %s nouns." % str(len(nouns)),
                 u"verbose"
                 )
    #Load list of verbs
    global verbs
    verbs = []
    for row in Willie.db.prompt_verbs.keys():
        verbs.append(Willie.db.prompt_verbs.get(row[0], 'verb'))
    Willie.debug(u"prompt.py",
                 u"Loaded %s verbs." % str(len(verbs)),
                 u"verbose"
                 )


def weighted_choice(weighted):
    """Returns a random index from a list of tuples that contain
    (something, weight) where weight is the weighted probablity that
    that item should be chosen. Higher weights are chosen more often"""

    sum = 0
    sum_steps = []
    for item in weighted:
        sum = sum + int(item[1])
        sum_steps.append(sum)
    return bisect.bisect_right(sum_steps, random.uniform(0, sum))


@commands(u'prompt')
def prompt(Willie, trigger):
    """Gives a short drawing prompt using ponies from the show."""

    Willie.debug(u"prompt.py", u"==============", u"verbose")
    Willie.debug(u"prompt.py", u"Module started", u"verbose")
    #Make our random selections for our prompt construction
    index_no = weighted_choice(ponies)
    sentence = [u"Your random prompt is: ",
                ponies[index_no][0],
                random.choice(verbs).strip(),
                random.choice(nouns).strip() + u"."
                ]
    Willie.reply(u" ".join(sentence))


if __name__ == "__main__":
    print __doc__.strip()
