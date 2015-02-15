"""
prompt.py - A willie module that generates simple drawing ideas
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import bisect
import random

from willie.logger import get_logger
from willie.module import commands

LOGGER = get_logger(__name__)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    import os.path
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()

random.seed()


def setup(bot):
    # Load list of names
    if 'prompt' not in bot.memory:
        bot.memory['prompt'] = {}
    if 'ponies' not in bot.memory['prompt']:
        bot.memory['prompt']['ponies'] = []
    if 'nouns' not in bot.memory['prompt']:
        bot.memory['prompt']['nouns'] = []
    if 'verbs' not in bot.memory['prompt']:
        bot.memory['prompt']['verbs'] = []

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
                bot.memory['prompt']['ponies'].append((n, w))
            dbload = None
        LOGGER.info(log.format("Loaded %s weighted ponies."), str(len(bot.memory['prompt']['ponies'])))

        cur.execute('SELECT * FROM prompt_nouns')
        dbload = cur.fetchall()
        if dbload:
            for n in dbload:
                bot.memory['prompt']['nouns'].append(n[0])
            dbload = None
        LOGGER.info(log.format("Loaded %s nouns."), str(len(bot.memory['prompt']['nouns'])))

        cur.execute('SELECT * FROM prompt_verbs')
        dbload = cur.fetchall()
        if dbload:
            for v in dbload:
                bot.memory['prompt']['verbs'].append(v[0])
            dbload = None
        LOGGER.info(log.format("Loaded %s verbs."), str(len(bot.memory['prompt']['verbs'])))
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


@commands('prompt')
def prompt(bot, trigger):
    """Gives a simple drawing prompt using random words and ponies from the show."""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    LOGGER.info(log.format("=============="))
    LOGGER.info(log.format("Module started"))
    # Make our random selections for our prompt construction
    index_no = weighted_choice(bot.memory['prompt']['ponies'])
    sentence = ["Your random prompt is: ",
                bot.memory['prompt']['ponies'][index_no][0],
                random.choice(bot.memory['prompt']['verbs']).strip(),
                random.choice(bot.memory['prompt']['nouns']).strip() + "."
                ]
    bot.reply(" ".join(sentence))


if __name__ == "__main__":
    print(__doc__.strip())
