"""
hugs.py - A simple Willie Module for interacting with 'hug' actions
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import re
import time

random.seed()

def hugback(Willie, trigger):
    """Returns a 'hug' action directed at the bot."""
    Willie.action('hugs %s back' % trigger.nick)
# Rules allow regex matches to PRIVMSG
hugback.rule = r'((($nickname)\s?((a.*? hug)|(hugs)))|' + \
        '(((a.*? hug)|(hugs))\s?($nickname)))'
# Priorities of 'high', 'medium', and 'low' work
hugback.priority = 'medium'
# Willie is multithreaded by default.
#hugback.thread = False
# Limit in seconds of users ability to trigger module
hugback.rate = 30

def hug_intercept(Willie, trigger):
    """Intercepts hugs from another bot"""
    Willie.debug("hugback.py:hug_intercept", "Caught hug.", "verbose")
    # First make sure we're intercepting the proper user's actions
    if re.match("hushmachine", trigger.nick):
        #Hugs directed at the bot
        if re.match("\001ACTION\s.+?%s.+?" % Willie.nick, trigger.args[1]):
            time.sleep(1)
            Willie.say(random.choice([":D","Aww, thanks!"]))
        #special hugging
        elif re.match("\001ACTION\sdrags.+?into the closet", trigger.args[1]):
            if random.uniform(0,1) < 0.5:
                time.sleep(1)
                if random.uniform(0,1) < 0.9:
                    Willie.say(random.choice(["[](/ww20)","Oh my..."]))
                else:
                    Willie.say("I wish someone would 'special hug' me... :(")
        #spaghetti
        elif re.match("\001ACTION\snervously hugs .*? fanny", trigger.args[1]):
            if random.uniform(0,1) < 0.5:
                time.sleep(1)
                Willie.action(
                    "sneaks over and nicks %s's " % trigger.nick + \
                    "fanny pack"
                    )
        #posts
        elif re.match("\001ACTION\sstarts a hug, but the", trigger.args[1]):
            if random.uniform(0,1) < 5:
                time.sleep(1)
                Willie.say("Yikes!")
                time.sleep(1)
                Willie.action(
                        "hands " + \
                        "%s a towel." % trigger.args[1].split()[19].rstrip(
                                "s").rstrip("'")
                        )
        # generic hugs
        # use the intersection of sets to exclude some responses
        elif re.match(
                "\001ACTION\s(.*?hug(s?).*?((\!)|(\.+)))", trigger.args[1]
                ) \
            and not set(trigger.args[1].split()).intersection(set([
                                "headbutts", "spaghetti", "vomits",
                                "trembling", "longer", "wallet.\001",
                                "fish", "tackles"
                                ])):
            Willie.debug("","inner trigger","verbose")
            if random.uniform(0,1) < 0.08:
                Willie.action(random.choice([
                    "quickly jumps in between and gets the hug instead.",
                    "shoves %s out of the way so she can " % trigger.nick + \
                            "give the hug instead.",
                    "steps in front of %s and " % trigger.nick + \
                            "affectionately hugs her in a way that only " + \
                            "two bots in love can manage."
                    ]))
        #smelling distance
        elif re.match("\001ACTION\sgets just within", trigger.args[1]):
            if random.uniform(0,1) < 0.5:
                time.sleep(1)
                Willie.action("slowly backs away from the stench.")
        #too long
        elif re.match("\001ACTION\sholds on to", trigger.args[1]):
            if random.uniform(0,1) < 0.5:
                time.sleep(2)
                Willie.action("joins the hug, but it just makes things worse.")
        #!no
        elif re.match("\001ACTION\s\!no", trigger.args[1]):
            time.sleep(1)
            Willie.say(random.choice([":o hushmachine!","Oh my...","lol"]))
# Rules allow regex matches to PRIVMSG
hug_intercept.rule = \
        "\001ACTION\s(" + \
        "(.*?hug(s?).*?((\!)|(\.+)))|" + \
        "(\!no)|" + \
        "(gets just within)|" + \
        "(hesitates a bit too long)|" + \
        "(holds on to)|" + \
        "(joins.+?in)" + \
        ")"
# Priorities of 'high', 'medium', and 'low' work
hug_intercept.priority = 'medium'
# Willie is multithreaded by default.
hug_intercept.thread = False

if __name__ == "__main__":
    print __doc__.strip()
