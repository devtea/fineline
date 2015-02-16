"""
hugs.py - A simple willie Module for interacting with 'hug' actions
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import re
import time

from willie.logger import get_logger
from willie.module import rule, rate

LOGGER = get_logger(__name__)

random.seed()

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


@rule(r'\001ACTION [a-zA-Z0-9 ,]*?' +
      r'((\bhugs? $nickname)|(\bgives $nickname a hug))')
@rate(90)
def hugback(bot, trigger):
    """Returns a 'hug' action directed at the bot."""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    bot.action(random.choice([
        'hugs %s back' % trigger.nick,
        'returns the hug',
        'grips %s tightly' % trigger.nick,
        'holds on for too long, mumbling something about warmth.'
    ]))


@rule("\001ACTION\s(" +
      "(.*?hug(s?).*?((\!)|(\.+)))|" +
      "(\!no)|" +
      "(gets just within)|" +
      "(hesitates a bit too long)|" +
      "(holds on to)|" +
      "(joins.+?in)" +
      ")"
      )
def hug_intercept(bot, trigger):
    """Intercepts hugs from another bot"""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    LOGGER.info(log.format("Caught hug."))
    # First make sure we're intercepting the proper user's actions
    if re.match("hushmachine", trigger.nick):
        # Hugs directed at the bot
        if re.match("\001ACTION\s.+?%s.+?" % bot.nick, trigger.args[1]):
            time.sleep(1)
            bot.say(random.choice([":D", "Aww, thanks!"]))
        elif re.findall(bot.nick, trigger.args[1]):
            return
        # special hugging
        elif re.match("\001ACTION\sdrags.+?into the closet", trigger.args[1]):
            if random.uniform(0, 1) < 0.5:
                time.sleep(1)
                if random.uniform(0, 1) < 0.9:
                    bot.say(random.choice(["[](/ww20)", "Oh my..."]))
                else:
                    bot.say("I wish someone would 'special hug' me... :(")
        # spaghetti
        elif re.match("\001ACTION\snervously hugs .*? fanny",
                      trigger.args[1]
                      ):
            if random.uniform(0, 1) < 0.5:
                time.sleep(1)
                bot.action(
                    "sneaks over and nicks %s's " % trigger.nick +
                    "fanny pack"
                )
        # posts
        elif re.match("\001ACTION\sstarts a hug, but the", trigger.args[1]):
            if random.uniform(0, 1) < 5:
                time.sleep(1)
                bot.say("Yikes!")
                time.sleep(2)
                bot.action(
                    "hands " +
                    "%s a towel." % trigger.args[1].split()[19].rstrip(
                        "s").rstrip("'")
                )
        # generic hugs
        # use the intersection of sets to exclude some responses
        elif re.match(
                "\001ACTION\s(.*?hug(s?).*?((\!)|(\.+)))", trigger.args[1]
        ) and not set(trigger.args[1].split()).intersection(set([
                "headbutts",
                "spaghetti",
                "vomits",
                "trembling",
                "longer",
                "wallet.\001",
                "fish",
                "tackles"
        ])):
            LOGGER.info(log.format("inner trigger"))
            if random.uniform(0, 1) < 0.04:
                bot.action(random.choice([
                    "quickly jumps in between them and gets the hug instead.",
                    "leaps over and shoves %s out of the " % trigger.nick +
                    "way so she can give the hug instead.",
                    "intercepts %s and " % trigger.nick +
                    "affectionately hugs him in a way that only " +
                    "two bots in love can manage."
                ]))
        # smelling distance
        elif re.match("\001ACTION\sgets just within", trigger.args[1]):
            if random.uniform(0, 1) < 0.5:
                time.sleep(1)
                bot.action("slowly backs away from the stench.")
        # too long
        elif re.match("\001ACTION\sholds on to", trigger.args[1]):
            if random.uniform(0, 1) < 0.5:
                time.sleep(2)
                bot.action("joins the hug, but it just makes things worse.")
        # !no
        elif re.match("\001ACTION\s\!no", trigger.args[1]):
            time.sleep(1)
            bot.say(random.choice([
                ":o hushmachine!",
                "Oh my...",
                "lol"]))


if __name__ == "__main__":
    print(__doc__.strip())
