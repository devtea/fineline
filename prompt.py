"""
prompt.py - A willie module that generates simple drawing ideas
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

import random
import bisect

from willie.module import commands

random.seed()

ponies = []
verbs = []
nouns = []


def setup(bot):
    #Load list of names
    global ponies
    ponies = []
    for row in bot.db.prompt_ponies.keys():
        ponies.append(bot.db.prompt_ponies.get(row[0], ('name', 'weight')))
    bot.debug(u"prompt.py",
              u"Loaded %s weighted ponies." % str(len(ponies)),
              u"verbose"
              )
    #Load list of nouns
    global nouns
    nouns = []
    for row in bot.db.prompt_nouns.keys():
        nouns.append(bot.db.prompt_nouns.get(row[0], 'noun'))
    bot.debug(u"prompt.py",
              u"Loaded %s nouns." % str(len(nouns)),
              u"verbose"
              )
    #Load list of verbs
    global verbs
    verbs = []
    for row in bot.db.prompt_verbs.keys():
        verbs.append(bot.db.prompt_verbs.get(row[0], 'verb'))
    bot.debug(u"prompt.py",
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
def prompt(bot, trigger):
    """Gives a short drawing prompt using ponies from the show."""

    bot.debug(u"prompt.py", u"==============", u"verbose")
    bot.debug(u"prompt.py", u"Module started", u"verbose")
    #Make our random selections for our prompt construction
    index_no = weighted_choice(ponies)
    sentence = [u"Your random prompt is: ",
                ponies[index_no][0],
                random.choice(verbs).strip(),
                random.choice(nouns).strip() + u"."
                ]
    bot.reply(u" ".join(sentence))


if __name__ == "__main__":
    print __doc__.strip()
