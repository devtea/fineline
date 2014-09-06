"""
prompt.py - A willie module that generates simple drawing ideas
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import random
import bisect

from willie.module import commands

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


random.seed()

ponies = []
verbs = []
nouns = []


def setup(bot):
    # Load list of names
    global ponies
    ponies = []
    global nouns
    nouns = []
    global verbs
    verbs = []

    dbcon = bot.db.connect()
    cur = dbcon.cursor()
    try:
        cur.execute('''CREATE TABLE IF NOT EXISTS prompt_ponies
                    (name TEXT, weight INTEGER)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS prompt_nouns
                    (noun TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS prompt_verbs
                    (verb TEXT)''')
        dbcon.commit()

        cur.execute('SELECT name, weight FROM prompt_ponies')
        dbload = cur.fetchall()
        if dbload:
            for n, w in dbload:
                ponies.append((n, w))
            dbload = None
        bot.debug(__file__, log.format(u"Loaded %s weighted ponies." % str(len(ponies))), u"verbose")

        cur.execute('SELECT * FROM prompt_nouns')
        dbload = cur.fetchall()
        if dbload:
            for n in dbload:
                nouns.append(n[0])
            dbload = None
        bot.debug(__file__, log.format(u"Loaded %s nouns." % str(len(nouns))), u"verbose")

        cur.execute('SELECT * FROM prompt_verbs')
        dbload = cur.fetchall()
        if dbload:
            for v in dbload:
                verbs.append(v[0])
            dbload = None
        bot.debug(__file__, log.format(u"Loaded %s verbs." % str(len(verbs))), u"verbose")
    finally:
        cur.close()
        dbcon.close()


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
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    bot.debug(__file__, log.format(u"=============="), u"verbose")
    bot.debug(__file__, log.format(u"Module started"), u"verbose")
    # Make our random selections for our prompt construction
    index_no = weighted_choice(ponies)
    sentence = [u"Your random prompt is: ",
                ponies[index_no][0],
                random.choice(verbs).strip(),
                random.choice(nouns).strip() + u"."
                ]
    bot.reply(u" ".join(sentence))


if __name__ == "__main__":
    print(__doc__.strip())
