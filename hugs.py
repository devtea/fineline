"""
hugs.py - A simple Willie Module for interacting with 'hug' actions
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import re
import time

from willie.module import rule, rate

random.seed()


@rule(u'\001ACTION [a-zA-Z0-9 ,]*?' +
      u'((hugs? $nickname)|(gives $nickname a hug))')
@rate(90)
def hugback(Willie, trigger):
    """Returns a 'hug' action directed at the bot."""
    Willie.action(random.choice([
        u'hugs %s back' % trigger.nick,
        u'returns the hug',
        u'grips %s tightly' % trigger.nick,
        u'holds on for too long, mumbling something about warmth.'
    ]))


@rule(u"\001ACTION\s(" +
      u"(.*?hug(s?).*?((\!)|(\.+)))|" +
      u"(\!no)|" +
      u"(gets just within)|" +
      u"(hesitates a bit too long)|" +
      u"(holds on to)|" +
      u"(joins.+?in)" +
      u")"
      )
def hug_intercept(Willie, trigger):
    """Intercepts hugs from another bot"""
    Willie.debug(u"hugback.py:hug_intercept", u"Caught hug.", u"verbose")
    # First make sure we're intercepting the proper user's actions
    if re.match("hushmachine", trigger.nick):
        #Hugs directed at the bot
        if re.match(u"\001ACTION\s.+?%s.+?" % Willie.nick, trigger.args[1]):
            time.sleep(1)
            Willie.say(random.choice([u":D", u"Aww, thanks!"]))
        elif re.findall(Willie.nick, trigger.args[1]):
            return
        #special hugging
        elif re.match(u"\001ACTION\sdrags.+?into the closet", trigger.args[1]):
            if random.uniform(0, 1) < 0.5:
                time.sleep(1)
                if random.uniform(0, 1) < 0.9:
                    Willie.say(random.choice([u"[](/ww20)", u"Oh my..."]))
                else:
                    Willie.say(u"I wish someone would 'special hug' me... :(")
        #spaghetti
        elif re.match(u"\001ACTION\snervously hugs .*? fanny",
                      trigger.args[1]
                      ):
            if random.uniform(0, 1) < 0.5:
                time.sleep(1)
                Willie.action(
                    u"sneaks over and nicks %s's " % trigger.nick +
                    u"fanny pack"
                )
        #posts
        elif re.match(u"\001ACTION\sstarts a hug, but the", trigger.args[1]):
            if random.uniform(0, 1) < 5:
                time.sleep(1)
                Willie.say(u"Yikes!")
                time.sleep(2)
                Willie.action(
                    u"hands " +
                    u"%s a towel." % trigger.args[1].split()[19].rstrip(
                        "s").rstrip("'")
                )
        # generic hugs
        # use the intersection of sets to exclude some responses
        elif re.match(
                u"\001ACTION\s(.*?hug(s?).*?((\!)|(\.+)))", trigger.args[1]
        ) and not set(trigger.args[1].split()).intersection(set([
                u"headbutts",
                u"spaghetti",
                u"vomits",
                u"trembling",
                u"longer",
                u"wallet.\001",
                u"fish",
                u"tackles"
        ])):
            Willie.debug(u"", u"inner trigger", u"verbose")
            if random.uniform(0, 1) < 0.08:
                Willie.action(random.choice([
                    u"quickly jumps in between them and gets the hug instead.",
                    u"leaps over and shoves %s out of the " % trigger.nick +
                    u"way so she can give the hug instead.",
                    u"intercepts %s and " % trigger.nick +
                    u"affectionately hugs him in a way that only " +
                    u"two bots in love can manage."
                ]))
        #smelling distance
        elif re.match(u"\001ACTION\sgets just within", trigger.args[1]):
            if random.uniform(0, 1) < 0.5:
                time.sleep(1)
                Willie.action(u"slowly backs away from the stench.")
        #too long
        elif re.match(u"\001ACTION\sholds on to", trigger.args[1]):
            if random.uniform(0, 1) < 0.5:
                time.sleep(2)
                Willie.action(u"joins the hug, " +
                              "but it just makes things worse."
                              )
        #!no
        elif re.match(u"\001ACTION\s\!no", trigger.args[1]):
            time.sleep(1)
            Willie.say(random.choice([u":o hushmachine!",
                                      u"Oh my...",
                                      u"lol"
                                      ]))


if __name__ == "__main__":
    print __doc__.strip()
