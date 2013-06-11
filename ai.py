"""
ai.py - A simple Willie module for misc silly ai
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import time
import random
import re

random.seed()


def derp(Willie, trigger):
    '''Sometimes replies to messages with 'derp' in them.'''
    if trigger.owner:
        prob = 1
    else:
        prob = 0.1
    if random.uniform(0,1) < prob:
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
    if not set(trigger.args[1].lower().split()).intersection(set(['not','no','at'])):
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
        "([A-Za-z0-9,.!\s]*?(%s)[^A-Za-z0-9]([A-Za-z0-9,.!\s]*?$nickname))" % basic_thanks
        )
ty.priority = 'medium'


basic_woo = "(wo[o]+[t]?)|(y[a]+y)|(whe[e]+)"
def woo(Willie, trigger):
    '''Sometimes replies to a woo with an emote'''
    if trigger.owner:
        prob = 1
    else:
        prob = 0.1
    if random.uniform(0,1) < prob:
        time.sleep(random.uniform(1,3))
        Willie.say(random.choice([
                "[](/flutteryay",
                "[](/ppwooo",
                "[](/flutterwoo",
                "[](/woonadance",
                "[](/raritywooo",
                "[](/ajyay",
                "[](/derpydance"
            ]) + ' "%s")' % re.search(basic_woo, trigger.bytes, flags=re.I).group())
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


def hi(Willie, trigger):
    """Replies to greetings."""
    message = random.choice(("Hi","Hello","Yo","Hey","Ahoy"))
    punctuation = random.choice((".","","!"))
    time.sleep(random.uniform(0,3))
    if random.uniform(0,1) > 0.5:
        Willie.reply(message + punctuation)
    else:
        Willie.say(message + " " + trigger.nick + punctuation)
prefix = r"($nickname[:,]?\s+)"
meat = r"(hello|hi|ahoy|sup|hey|yo|afternoon|morning)"
all = r"(all|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
        "folks|guys|peoples?|$nickname)"
to_fineline = prefix + meat + '([.!\s]?$)'
to_all =  meat + r"[,]?\s+" + all + '([.!\s]?$)'
# Rules allow regex matches to PRIVMSG
hi.rule = r"(" + to_fineline + r")|" + \
        r"(" + to_all + r")"
hi.priority = 'medium'
hi.rate = 300


def isbot(Willie, trigger):
    """Replies to queries about fineline being a bot"""
    time.sleep(random.uniform(1,2))
    Willie.say(random.choice(("Nope, I'm just fast.",
            "Nah, I just type really fast and know a lot.",
            "What makes you think that?",
            "lolno",
            "Uh.....no?"
            )))
    time.sleep(random.uniform(3,5))
    Willie.say(random.choice(("And I have hooves!",
            "If I were a bot, how come I have hooves?",
            "See? I have hooves! *wiggles hooves*"
            )))
isbot.rule = r'.*$nickname\:?,?\s+Are you a bot|.*$nickname (is )?a bot'
isbot.priority = 'medium'
isbot.rate = 300


def night(Willie, trigger):
    """Responds to people saying good night"""
    if re.match('.*?night', trigger.bytes):
        message = random.choice(("Goodnight", "'Night", "Later", "Bye"))
    else:
        message = random.choice(("Later", "Bye"))
    punctuation = random.choice((".","","!"))
    # Test statment to filter negetive statements
    Willie.debug("ai_night.py:night", trigger.bytes, "verbose")
    # Use a set intersection to filter triggering lines by keyword
    if not set(trigger.args[1].lower().split()).intersection(set(['not','no','at'])):
        time.sleep(1)
        if random.uniform(0,1) > 0.5:
            Willie.reply(message + punctuation)
        else:
            Willie.say(message + " " + trigger.nick + punctuation)
prefix = r"($nickname\:?,?\s+)"
meat = r"((good|g)?\s?'?(night|bye)|(later(s?)))"
all = r"(all|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
        "folks|guys|peoples?|$nickname)"
to_fineline = prefix + meat
to_all = r".*?" + meat + r",?\s+" + all
universal = r".*?((time (for me)?\s?(to|for)\s?((go to)|(head))?\s?(to )?" + \
            "(bed|sleep))|" + \
            "(I'?m ((((going to)|(gonna)) ((go)|(head off))?)|(heading off))\s?(to )?(bed|sleep|crash|(pass out))))"
night.rule = r"(" + to_fineline + r")|" + \
        r"(" + to_all + r")|" + \
        r"(" + universal + r")"
night.priority = 'high'
night.rate = 1000


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
