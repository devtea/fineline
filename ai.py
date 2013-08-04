# coding=utf8
"""
ai.py - A simple Willie module for misc silly ai
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import time
import random
import re
from willie.tools import Nick

from willie.module import rule, rate, priority

basic_thanks = u"ty|thanks|gracias|thank\s?you|thank\s?ya|ta"
basic_woo = u"(wo[o]+[t]?)|(y[a]+y)|(whe[e]+)"
basic_badbot = (u"bad|no|stop|dam[nit]+?|ffs|stfu|shut (it|up)|don'?t|wtf|" +
                u"(fuck[s]?\s?(sake|off)?)")
n_text = u"[A-Za-z0-9,.'!\s]"
basic_slap = u"slap[p]?[s]?|hit[s]?|smack[s]?\b"
random.seed()


@rule(u'^[A-Za-z0-9)(/\s]*?\s?derp')
def derp(Willie, trigger):
    '''Sometimes replies to messages with 'derp' in them.'''
    if trigger.owner:
        prob = 1
    else:
        prob = 0.1
    if random.uniform(0, 1) < prob:
        time.sleep(random.uniform(1, 3))
        Willie.say(random.choice([
            u"[](/derpwizard)",
            u"[](/derpwizard)",
            u"[](/derpout)",
            u"[](/derpshrug)",
            u"[](/derpwat)",
            u"[](/derpsrs)",
            u"[](/derpyhuh)",
            u"[](/derpypeek)",
            u"[](/fillyderp)"
        ]))


@rule(
    u"(^$nickname[,:\s]\s(%s)($|[\s,.!]))|" % basic_thanks +
    (u"([A-Za-z0-9,.!\s]*?(%s)[^A-Za-z0-9]" +
    u"([A-Za-z0-9,.!\s]*?$nickname))") % basic_thanks
)
def ty(Willie, trigger):
    '''Politely replies to thank you's.'''
    if not set(trigger.args[1].lower().split()).intersection(set([u'not',
                                                                  u'no',
                                                                  u'at'])):
        time.sleep(random.uniform(1, 3))
        Willie.reply(
            random.choice([
                u"Yep",
                u"You're welcome",
                u"Certainly",
                u"Of course",
                u"Sure thing"
            ]) +
            random.choice([".", "!"])
        )


@rule(u'^[A-Za-z0-9)(/\s]*?\s?(%s)([^A-Za-z]|h[o]+|$)' % basic_woo)
def woo(Willie, trigger):
    '''Sometimes replies to a woo with an emote'''
    if trigger.owner:
        prob = 1
    else:
        prob = 0.1
    if random.uniform(0, 1) < prob:
        time.sleep(random.uniform(1, 3))
        Willie.say(
            random.choice([
                u"[](/flutteryay",
                u"[](/ppwooo",
                u"[](/flutterwoo",
                u"[](/woonadance",
                u"[](/raritywooo",
                u"[](/ajyay",
                u"[](/derpydance"
            ]) + u' "%s")' % re.search(
                basic_woo,
                trigger.bytes,
                flags=re.I
            ).group()
        )


@rule(
    u"(((^|%s+?\s)$nickname[.,-:]\s(%s+?\s)?(%s)([^A-Za-z0-9]|$))|" % (
    n_text, n_text, basic_badbot) +
    u"((^|%s+?\s)((%s)\s)(%s*?\s)?$nickname([^A-Za-z0-9]|$))|" % (
        n_text, basic_badbot, n_text) +
    u"(($nickname%s+?)(%s)([^A-Za-z0-9]|$)))" % (n_text, basic_badbot)
)
def badbot(Willie, trigger):
    '''Appropriate replies to chastening'''
    time.sleep(random.uniform(1, 3))
    if trigger.owner:
        Willie.say(random.choice([
            u"[](/sadderpy)",
            u"[](/raritysad)",
            u"[](/sadtwilight2)",
            u"[](/scootasad)",
            u"[](/seriouslysadaj)",
            u"[](/dashiesad)",
            u"[](/fscry)",
            u"[](/aj05)",
            u"[](/pinkiefear)"
        ]))
    elif Nick(trigger.nick) == Nick('DarkFlame'):
        Willie.say(random.choice([
            u'[](/ppnowhy "Why are you so mean to me?!")',
            u'[](/ppnowhy "Why do you hate me?!")'
            u'[](/ppnowhy "Why is nothing I do ever good enough for you?!")'
            u'[](/ppnowhy "?!")'
        ]))
    elif random.uniform(0, 1) < 0.1:
        Willie.reply(random.choice([
            u"[](/derpsrs)",
            u"[](/cheersrsly)",
            u"[](/fluttersrs)",
            u"[](/cewat)",
            u"[](/lyrawat)",
            u"[](/ppwatching)",
            u"[](/watchout)",
            u"[](/dashiemad)",
            u"[](/ppumad)"
        ]))


@rule(u"^!swo[o]+sh")
def swish(Willie, trigger):
    if random.uniform(0, 1) < 0.1:
        time.sleep(random.uniform(1, 3))
        Willie.debug(u"swoosh", trigger.group(0), u"verbose")
        i = u"i" * (len(trigger.group(0)) - 5)
        Willie.say(u"[](/dhexcited) Sw%ssh! ♥" % i)


@rule(
    u"(^!(%s))|" % basic_slap +
    u"(\001ACTION [A-Za-z0-9,.'!\s]*?(%s)" % basic_slap +
    u"[A-Za-z0-9,.'!\s]+?$nickname)|" +
    u"(\001ACTION [A-Za-z0-9,.'!\s]+?$nickname" +
    u"[A-Za-z0-9,.'!\s]*?(%s)$)" % basic_slap
)
def slapped(Willie, trigger):
    time.sleep(random.uniform(1, 3))
    Willie.reply(random.choice([
        u'Stop that!',
        u'Hey!',
        u'Violence is not the answer!',
        u"Didn't your mother teach you not to hit?"
    ]))
    Willie.reply(u"[](/pinkieslap)")


hi_prefix = ur"($nickname[:,]?\s+)"
hi_meat = ur"(hello|hi|ahoy|sup|hey|yo|afternoon|morning)"
hi_all = ur"(all|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
    ur"folks|guys|peoples?|$nickname)"
hi_to_fineline = hi_prefix + hi_meat + u'([.!\s]?$)'
hi_to_all = hi_meat + ur"[,]?\s+" + hi_all + u'([.!\s]?$)'


@rule(ur"(" + hi_to_fineline + ur")|" + ur"(" + hi_to_all + ur")")
@rate(300)
def hi(Willie, trigger):
    """Replies to greetings."""
    message = random.choice([u"Hi", u"Hello", u"Yo", u"Hey", u"Ahoy"])
    punctuation = random.choice([u".", u"", u"!"])
    time.sleep(random.uniform(0, 3))
    if random.uniform(0, 1) > 0.5:
        Willie.reply(message + punctuation)
    else:
        Willie.say(message + u" " + trigger.nick + punctuation)


@rule(ur'.*$nickname\:?,?\s+Are you a bot|.*$nickname (is )?a bot')
@rate(300)
def isbot(Willie, trigger):
    """Replies to queries about fineline being a bot"""
    time.sleep(random.uniform(1, 2))
    Willie.say(random.choice(
        [u"Nope, I'm just fast.",
         u"Nah, I just type really fast and know a lot.",
         u"What makes you think that?",
         u"lolno",
         u"Uh.....no?"]
    ))
    time.sleep(random.uniform(3, 5))
    Willie.say(random.choice(
        [u"Come on, don't you see these hooves?",
         u"If I were a bot, how come I have hooves?",
         u"See? I have hooves! *wiggles hooves*",
         u"I'm kinda hurt you'd even suggest such a thing...",
         u"Are you a bot?",
         u"Besides, sentience is a hard thing to prove..."]
    ))


night_prefix = ur"($nickname\:?,?\s+)"
night_meat = ur"((good|g)?\s?'?(night|bye)|(later(s?)))"
night_all = ur"(all|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
    u"folks|guys|peoples?|$nickname)"
night_to_fineline = night_prefix + night_meat
night_to_all = ur".*?" + night_meat + ur",?\s+" + night_all
night_universal = ur".*?((time (for me)?\s?(to|for)\s?((go to)|(head))?\s?" + \
    u"(to )?(bed|sleep))|" + \
    u"(I'?m ((((going to)|(gonna)) ((go)|(head off))?)|(heading off))" + \
    u"\s?(to )?(bed|sleep|crash|(pass out))))"


@rule(
    ur"(" + night_to_fineline + ur")|" +
    ur"(" + night_to_all + ur")|" +
    ur"(" + night_universal + ur")"
)
@priority('high')
@rate(1000)
def night(Willie, trigger):
    """Responds to people saying good night"""
    if re.match(u'.*?night', trigger.bytes):
        message = random.choice([u"Goodnight", u"'Night", u"Later", u"Bye"])
    else:
        message = random.choice([u"Later", u"Bye"])
    punctuation = random.choice([u".", u"", u"!"])
    # Test statment to filter negetive statements
    Willie.debug(u"ai_night.py:night", trigger.bytes, u"verbose")
    # Use a set intersection to filter triggering lines by keyword
    if not set(trigger.args[1].lower().split()).intersection(set([u'not',
                                                                  u'no',
                                                                  u'at'
                                                                  ])):
        time.sleep(1)
        if random.uniform(0, 1) > 0.5:
            Willie.reply(message + punctuation)
        else:
            Willie.say(message + u" " + trigger.nick + punctuation)

"""
def smart_action(Willie, trigger):
    '''Hopefully a flexible, fun action system for admins'''
    Willie.debug("ai:derp", "triggered", "verbose")
    Willie.debug("ai:derp", trigger.nick, "verbose")
    Willie.debug("ai:derp", trigger.args, "verbose")
    Willie.debug("ai:derp", "admin: " + str(trigger.admin), "verbose")
    Willie.debug("ai:derp", "owner: " + str(trigger.owner), "verbose")
    Willie.debug("ai:derp", "isop: " + str(trigger.isop), "verbose")
basic_smart = "would you kindly|please|go"
smart_action.rule = ("^$nickname[:,\s]+(%s)[A-Za-z0-9,'\s]+(NICKNAME)" +
    "(a|an|the|some)(OBJECT)?")
smart_action.priority = 'medium'
"""


@rule(ur'^$nickname\s?[!\.]\s?$')
def nick(Willie, trigger):
    message = trigger.nick
    if re.match(Willie.nick.upper(), trigger.bytes):
        message = message.upper()
    if re.findall('!', trigger.bytes):
        Willie.say(u'%s!' % message)
    else:
        Willie.say(u'%s.' % message)


if __name__ == "__main__":
    print __doc__.strip()
