# coding=utf8
"""
ai.py - A simple willie module for misc silly ai
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function
import time
import random
import re
from willie.tools import Nick

from willie.module import rule, rate, priority

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

basic_thanks = r"\bty|thanks|gracias|thank\s?you|thank\s?ya|\bta"
basic_woo = r"(wo[o]+[t]?)|(y[a]+y)|(whe[e]+)\b"
basic_badbot = (u"bad|no|stop|dam[nit]+?|ffs|stfu|shut (it|up)|wtf|" +
                u"(fuck[s]?\s?(sake|off)?)")
n_text = u"[A-Za-z0-9,.'!\s]"
basic_slap = u"slap[p]?[s]?|hit[s]?|smack[s]?\b"
random.seed()


# @rule(u'^[A-Za-z0-9)(/\s]*?\s?derp')
@rule(r'^.*?\bderp\b')
def derp(bot, trigger):
    '''Sometimes replies to messages with 'derp' in them.'''
    if trigger.owner:
        prob = 1
    else:
        prob = 0.1
    if random.uniform(0, 1) < prob:
        time.sleep(random.uniform(1, 3))
        bot.say(random.choice([
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
def ty(bot, trigger):
    '''Politely replies to thank you's.'''
    if not set(trigger.args[1].lower().split()).intersection(set([u'not',
                                                                  u'no',
                                                                  u'at'])):
        time.sleep(random.uniform(1, 3))
        bot.reply(
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
def woo(bot, trigger):
    '''Sometimes replies to a woo with an emote'''
    if trigger.owner:
        prob = 1
    else:
        prob = 0.1
    if random.uniform(0, 1) < prob:
        time.sleep(random.uniform(1, 3))
        bot.say(
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
def badbot(bot, trigger):
    '''Appropriate replies to chastening'''
    time.sleep(random.uniform(1, 3))
    if trigger.owner:
        bot.say(random.choice([
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
        bot.say(random.choice([
            u'[](/ppnowhy "Why are you so mean to me?!")',
            u'[](/ppnowhy "Why do you hate me?!")',
            u'[](/ppnowhy "Why is nothing I do ever good enough for you?!")',
            u'[](/ppnowhy "?!")'
        ]))
    elif random.uniform(0, 1) < 0.1:
        bot.reply(random.choice([
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
def swish(bot, trigger):
    if random.uniform(0, 1) < 0.01:
        time.sleep(random.uniform(1, 3))
        bot.debug(__file__, log.format(trigger.group(0)), u"verbose")
        i = u"i" * (len(trigger.group(0)) - 5)
        bot.say(u"[](/dhexcited) Sw%ssh! ♥" % i)


@rule(
    u"(^!(%s))|" % basic_slap +
    u"(\001ACTION [A-Za-z0-9,.'!\s]*?(%s)" % basic_slap +
    u"[A-Za-z0-9,.'!\s]+?$nickname)|" +
    u"(\001ACTION [A-Za-z0-9,.'!\s]+?$nickname" +
    u"[A-Za-z0-9,.'!\s]*?(%s)$)" % basic_slap
)
def slapped(bot, trigger):
    time.sleep(random.uniform(1, 3))
    bot.reply(random.choice([
        u'Stop that!',
        u'Hey!',
        u'Violence is not the answer!',
        u"Didn't your mother teach you not to hit?"
    ]))
    bot.reply(u"[](/pinkieslap)")


hi_prefix = ur"($nickname[:,]?\s+)"
hi_meat = ur"(hello|hi|ahoy|sup|hey|yo|afternoon|morning)"
hi_all = ur"(all|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
    ur"folks|guys|peoples?|$nickname)"
hi_to_fineline = hi_prefix + hi_meat + u'([.!\s]?$)'
hi_to_all = hi_meat + ur"[,]?\s+" + hi_all + u'([.!\s]?$)'


@rule(ur"(" + hi_to_fineline + ur")|" + ur"(" + hi_to_all + ur")")
@rate(300)
def hi(bot, trigger):
    """Replies to greetings."""
    message = random.choice([u"Hi", u"Hello", u"Yo", u"Hey", u"Ahoy"])
    punctuation = random.choice([u".", u"", u"!"])
    time.sleep(random.uniform(0, 3))
    if random.uniform(0, 1) > 0.5:
        bot.reply(message + punctuation)
    else:
        bot.say(message + u" " + trigger.nick + punctuation)


@rule(ur'.*$nickname\:?,?\s+Are you a bot|.*$nickname (is )?a bot')
@rate(300)
def isbot(bot, trigger):
    """Replies to queries about fineline being a bot"""
    time.sleep(random.uniform(1, 2))
    bot.say(random.choice(
        [u"Nope, I'm just fast.",
         u"Nah, I just type really fast and know a lot.",
         u"What makes you think that?",
         u"lolno",
         u"Uh.....no?"]
    ))
    time.sleep(random.uniform(3, 5))
    bot.say(random.choice(
        [u"Come on, don't you see these hooves?",
         u"If I were a bot, how come I have hooves?",
         u"See? I have hooves! *wiggles hooves*",
         u"I'm kinda hurt you'd even suggest such a thing...",
         u"Are you a bot?",
         u"Though I have the oddest urge t- ERROR 418 I'M A TEAPOT!",
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
def night(bot, trigger):
    """Responds to people saying good night"""
    if re.match(u'.*?night', trigger.bytes):
        message = random.choice([u"Goodnight", u"'Night", u"Later", u"Bye"])
    else:
        message = random.choice([u"Later", u"Bye"])
    punctuation = random.choice([u".", u"", u"!"])
    # Test statment to filter negetive statements
    bot.debug(__file__, log.format(trigger.bytes), u"verbose")
    # Use a set intersection to filter triggering lines by keyword
    if not set(trigger.args[1].lower().split()).intersection(set([u'not', u'no', u'at'])):
        time.sleep(1)
        if random.uniform(0, 1) > 0.5:
            bot.reply(message + punctuation)
        else:
            bot.say(message + u" " + trigger.nick + punctuation)

"""
def smart_action(bot, trigger):
    '''Hopefully a flexible, fun action system for admins'''
    bot.debug(__file__, log.format("triggered"), "verbose")
    bot.debug(__file__, log.format(trigger.nick), "verbose")
    bot.debug(__file__, log.format(trigger.args), "verbose")
    bot.debug(__file__, log.format("admin: ", trigger.admin), "verbose")
    bot.debug(__file__, log.format("owner: ", trigger.owner), "verbose")
    bot.debug(__file__, log.format("isop: ",trigger.isop), "verbose")
basic_smart = "would you kindly|please|go"
smart_action.rule = ("^$nickname[:,\s]+(%s)[A-Za-z0-9,'\s]+(NICKNAME)" +
    "(a|an|the|some)(OBJECT)?")
smart_action.priority = 'medium'
"""


@rule(ur'^$nickname\s?[!\.]\s?$')
def nick(bot, trigger):
    message = trigger.nick
    if re.match(bot.nick.upper(), trigger.bytes):
        message = message.upper()
    if re.findall('!', trigger.bytes):
        bot.say(u'%s!' % message)
    else:
        bot.say(u'%s.' % message)


@rule(u'^\001ACTION awkwardly tries to flirt with Fineline.')
def flirt(bot, trigger):
    if trigger.nick != Nick('hushmachine'):
        return
    time.sleep(random.uniform(2, 5))
    if re.search("you come here often", trigger.bytes):
        response = random.choice([
            (False, 'Oh, every now and then.'),
            (False, "I don't think I've seen you around."),
            (True, 'backs away slowly.'),
            (False, "[](/pplie 'eenope!')"),
            (False, "What's a nice boy like you doing in a place like this?"),
            (True, 'blushes and mumbles something')
        ])
    elif re.search("see my collection", trigger.bytes):
        response = random.choice([
            (False, '[](/sbstare)'),
            (True, 'grabs the degausser and cackles maniacally.'),
            (True, 'follows hushmachine to the back room'),
            (False, 'um.....sure?'),
            (False, '01000010011000010110001001111001001000000110010001101111011011100010011101110100001000000110100001110101011100100111010000100000011011010110010100101110'),
            (False, 'Hmmm.... Why not?'),
            (False, '...'),
            (False, 'Ones and zeros, huh? I prefer trinary, thanks.'),
            (False, 'You show me yours, I\'ll show you mine... [](/ww20)'),
            (False, 'Is that a RAID6 in your pocket, or are you happy to see me?')
        ])
    if response[0]:
        bot.action(response[1])
    else:
        bot.say(response[1])

if __name__ == "__main__":
    print(__doc__.strip())
