"""
ai.py - A simple Willie module for misc silly ai
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import time
import random

def derp(Willie, trigger):
    '''Sometimes replies to messages with 'derp' in them.'''
    if random.uniform(0,1) < 0.1:
        time.sleep(random.uniform(1,3))
        Willie.say(random.choice([
            "[](/derpwizard)",
            "[](/derpwizard)",
            "[](/derpout)",
            "[](/derpshrug)",
            "[](/derpwat)",
            "[](/derpsrs)",
            "[](/derpyhuh)",
            "[](/derpypeek)",
            "[](/fillyderp)"
            ]))
derp.rule = ('^[A-Za-z0-9)(/\s]*?\s?derp')
derp.priority = 'medium'


def ty(Willie, trigger):
    '''Politely replies to thank you's.'''
    time.sleep(random.uniform(1,3))
    Willie.reply(
            random.choice([
                "Yep",
                "You're welcome",
                "Certainly",
                "Of course",
                "Sure thing"
            ]) +
            random.choice([".","!"])
            )
basic_thanks = "ty|thanks|gracias|thank\s?you|thank\s?ya|ta"
ty.rule = ("(^$nickname[,:\s]\s(%s)($|[\s,.!]))|" % basic_thanks +
        "([A-Za-z0-9,.!\s]*?(%s)([A-Za-z0-9,.!\s]+?$nickname))" % basic_thanks
        )
ty.priority = 'medium'


def woo(Willie, trigger):
    '''Sometimes replies to a woo with an emote'''
    if random.uniform(0,1) < 0.1:
        time.sleep(random.uniform(1,3))
        Willie.say(random.choice([
                "[](/flutteryay",
                "[](/ppwooo",
                "[](/flutterwoo",
                "[](/woonadance",
                "[](/raritywooo",
                "[](/ajyay",
                "[](/derpydance"
            ]) + ' "%s")' % trigger.group(0).strip())
basic_woo = "(wo[o]+[t]?)|(y[a]+y)"
woo.rule = ('^[A-Za-z0-9)(/\s]*?\s?(%s)([^A-Za-z]|h[o]+|$)') % basic_woo
woo.priority = 'medium'


def badbot(Willie, trigger):
    '''Appropriate replies to chastening'''
    time.sleep(random.uniform(1,3))
    if trigger.owner:
        Willie.say(random.choice([
                "[](/sadderpy)",
                "[](/raritysad)",
                "[](/sadtwilight2)",
                "[](/scootasad)",
                "[](/seriouslysadaj)",
                "[](/dashiesad)",
                "[](/fscry)",
                "[](/aj05)",
                "[](/pinkiefear)"
                ]))
    elif random.uniform(0,1) < 0.1:
        Willie.reply(random.choice([
            "[](/derpsrs)",
            "[](/cheersrsly)",
            "[](/fluttersrs)",
            "[](/cewat)",
            "[](/lyrawat)",
            "[](/ppwatching)",
            "[](/watchout)",
            "[](/dashiemad)",
            "[](/ppumad)"
            ]))
basic_badbot = ("bad|no|stop|dam[nit]+?|ffs|stfu|shut (it|up)|don'?t|wtf|" +
        "(fuck[s]?\s?(sake|off)?)")
n_text = "[A-Za-z0-9,.'!\s]"
badbot.rule = ("(((^|%s+?\s)$nickname[.,-:]\s(%s+?\s)?(%s)([^A-Za-z0-9]|$))|" % (n_text, n_text, basic_badbot) +
        "((^|%s+?\s)((%s)\s)(%s*?\s)?$nickname([^A-Za-z0-9]|$))|" % (n_text, basic_badbot, n_text) +
        "(($nickname%s+?)(%s)([^A-Za-z0-9]|$)))" % (n_text, basic_badbot)
        )
badbot.priority = 'medium'


def swish(Willie, trigger):
    if random.uniform(0,1) < 0.1:
        time.sleep(random.uniform(1,3))
        Willie.debug("swoosh", trigger.group(0), "verbose")
        i = "i"*(len(trigger.group(0))-5)
        Willie.say("[](/dhexcited) Sw%ssh! <3" % i)
swish.rule = "^!swo[o]+sh"
swish.priority = 'medium'

def slapped(Willie, trigger):
    time.sleep(random.uniform(1,3))
    Willie.reply("[](/pinkieslap)")
basic_slap = "slap[p]?[s]?|hit[s]?|smack[s]?"
slapped.rule = ("(^!?(%s))|" % basic_slap +
        "(\001ACTION [A-Za-z0-9,.'!\s]*?(%s)" % basic_slap +
                "[A-Za-z0-9,.'!\s]+?$nickname)|" +
        "(\001ACTION [A-Za-z0-9,.'!\s]+?$nickname" +
                "[A-Za-z0-9,.'!\s]*?(%s))" % basic_slap
        )
slapped.priority = 'medium'


def smart_action(Willie, trigger):
    '''Hopefully a flexible, fun action system for admins'''
    Willie.debug("ai:derp", "triggered", "verbose")
    Willie.debug("ai:derp", trigger.nick, "verbose")
    Willie.debug("ai:derp", trigger.args, "verbose")
    Willie.debug("ai:derp", "admin: " + str(trigger.admin), "verbose")
    Willie.debug("ai:derp", "owner: " + str(trigger.owner), "verbose")
    Willie.debug("ai:derp", "isop: " + str(trigger.isop), "verbose")
basic_smart = "would you kindly|please|go"
smart_action.rule = ("^$nickname[:,\s]+(%s)[A-Za-z0-9,'\s]+(NICKNAME)(a|an|the|some)(OBJECT)?")
smart_action.priority = 'medium'

if __name__ == "__main__":
    print __doc__.strip()
