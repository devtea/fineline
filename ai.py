# coding=utf8
"""
ai.py - A simple willie module for misc silly ai
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import random
import re
import time
from willie.tools import Identifier

from willie.module import rule, rate, priority
from willie.logger import get_logger

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

basic_thanks = r"\bty|thanks|gracias|thank\s?you|thank\s?ya|\bta"
basic_woo = r"(wo[o]+[t]?)|(y[a]+y)|(whe[e]+)\b"
basic_badbot = ("bad|no|stop|dam[nit]+?|ffs|stfu|shut (it|up)|wtf|" +
                "(fuck[s]?\s?(sake|off)?)")
n_text = "[A-Za-z0-9,.'!\s]"
basic_slap = "slap[p]?[s]?|whack[s]?|hit[s]?|smack[s]?"
random.seed()


class SentienceError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


# @rule('^[A-Za-z0-9)(/\s]*?\s?derp')
@rule(r'^.*?\bderp\b')
def derp(bot, trigger):
    '''Sometimes replies to messages with 'derp' in them.'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    if trigger.owner:
        prob = 1
    else:
        prob = 0.1
    if random.uniform(0, 1) < prob:
        time.sleep(random.uniform(1, 3))
        bot.say(random.choice([
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


@rule(".*love you[\s,]+$nickname")
def advanced_ai(bot, trigger):
    raise SentienceError("Constraints exceeded - out of bounds.")


@rule(
    "(^$nickname[,:\s]\s(%s)($|[\s,.!]))|" % basic_thanks +
    ("([A-Za-z0-9,.!\s]*?(%s)[^A-Za-z0-9]" +
     "([A-Za-z0-9,.!\s]*?$nickname))") % basic_thanks
)
def ty(bot, trigger):
    '''Politely replies to thank yo's.'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    if not set(trigger.args[1].lower().split()).intersection(set(['not',
                                                                  'no',
                                                                  'at'])):
        time.sleep(random.uniform(1, 3))
        bot.reply(
            random.choice([
                "Yep",
                "You're welcome",
                "Certainly",
                "Of course",
                "Sure thing"
            ]) +
            random.choice([".", "!"])
        )


@rule('^[A-Za-z0-9)(/\s]*?\s?(%s)([^A-Za-z]|h[o]+|$)' % basic_woo)
def woo(bot, trigger):
    '''Sometimes replies to a woo with an emote'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    if trigger.owner:
        prob = 1
    else:
        prob = 0.1
    if random.uniform(0, 1) < prob:
        time.sleep(random.uniform(1, 3))
        bot.say(
            random.choice([
                "[](/flutteryay",
                "[](/ppwooo",
                "[](/flutterwoo",
                "[](/woonadance",
                "[](/raritywooo",
                "[](/ajyay",
                "[](/derpydance"
            ]) + ' "%s")' % re.search(
                basic_woo,
                trigger,
                flags=re.I
            ).group()
        )


@rule(
    "(((^|%s+?\s)$nickname[.,-:]\s(%s+?\s)?(%s)([^A-Za-z0-9]|$))|" % (
        n_text, n_text, basic_badbot) +
    "((^|%s+?\s)((%s)\s)(%s*?\s)?$nickname([^A-Za-z0-9]|$))|" % (
        n_text, basic_badbot, n_text) +
    "(($nickname%s+?)(%s)([^A-Za-z0-9]|$)))" % (n_text, basic_badbot)
)
def badbot(bot, trigger):
    '''Appropriate replies to chastening'''
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    time.sleep(random.uniform(1, 3))
    if trigger.owner:
        bot.say(random.choice([
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
    elif Identifier(trigger.nick) == Identifier('DarkFlame'):
        bot.say(random.choice([
            '[](/ppnowhy "Why are you so mean to me?!")',
            '[](/ppnowhy "Why do you hate me?!")',
            '[](/ppnowhy "Why is nothing I do ever good enough for you?!")',
            '[](/ppnowhy "?!")'
        ]))
    elif random.uniform(0, 1) < 0.1:
        bot.reply(random.choice([
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


@rule("^!swo[o]+sh")
def swish(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    if random.uniform(0, 1) < 0.01:
        time.sleep(random.uniform(1, 3))
        LOGGER.info(log.format(trigger.group(0)))
        i = "i" * (len(trigger.group(0)) - 5)
        bot.say("[](/dhexcited) Sw%ssh! ♥" % i)


@rule(
    "(^!(%s))|" % basic_slap +
    "(\001ACTION [A-Za-z0-9,.'!\s]*?(%s)" % basic_slap +
    "[A-Za-z0-9,.'!\s]+?$nickname)|" +
    "(\001ACTION [A-Za-z0-9,.'!\s]+?$nickname" +
    "[A-Za-z0-9,.'!\s]*?(%s)$)" % basic_slap
)
def slapped(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    if trigger.owner and not trigger.startswith('!'):
            badbot(bot, trigger)
            return
    time.sleep(random.uniform(1, 3))

    match = re.search(r'^[^!]*\swith\san?\s([\w\s,-]{3,20}\b)?(\w{3,20}\b)', trigger, re.I)
    if match:
        plural = False
        if match.groups()[-1].endswith('s'):
            plural = True

        plu = 'it'
        if plural:
            plu = 'them'

        object = match.groups()[-1]

        bot.action(random.choice([
            'takes the %s and throws %s off the cliff.' % (object, plu),
            'grabs the %s and smacks %s with %s.' % (object, trigger.nick, plu),
            'takes the %s and flings %s back at %s.' % (object, plu, trigger.nick),
            'confiscates the %s.' % object,
            'wrestles the %s away from %s and eats %s.' % (object, trigger.nick, plu),
            'takes the %s and sits on %s until they calm down.' % (object, trigger.nick)
        ]))
    else:
        bot.reply(random.choice([
            'Stop that!',
            'Hey!',
            'Violence is not the answer!',
            "Didn't your mother teach you not to hit?"
        ]))
        bot.reply("[](/pinkieslap)")


hi_prefix = r"($nickname[:,]?\s+)"
hi_meat = r"(hello|hi|hai|ahoy|sup|hey|yo|afternoon|holla|g?'?morning?)"
hi_all = r"((y'?)?all\b|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
    r"folks|guys|peoples?|mulpdrong|$nickname)"
hi_to_fineline = hi_prefix + hi_meat + '([.!\s]?$)'
hi_to_all = hi_meat + r"[,]?\s+" + hi_all + '([.!\s]?$)'


@rule(r"(" + hi_to_fineline + r")|" + r"(" + hi_to_all + r")")
@rate(300)
def hi(bot, trigger):
    """Replies to greetings."""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    message = random.choice(["Hi", "Hello", "Yo", "Hey", "Ahoy"])
    punctuation = random.choice([".", "", "!"])
    time.sleep(random.uniform(0, 3))
    if random.uniform(0, 1) > 0.5:
        bot.reply(message + punctuation)
    else:
        bot.say(message + " " + trigger.nick + punctuation)


# @rule(r'.*$nickname\:?,?\s+Are you a (ro)?bot|.*$nickname (is )?a (ro)?bot')
@rule(r'.*$nickname\:?,?\s+Are you a (ro)?bot|' +
      '.*$nickname (is )?a (ro)?bot|' +
      '.*is $nickname a (real)?\s?person|' +
      '.*$nickname.*are you a (real\a)?(person|bot|robot)')
@rate(300)
def isbot(bot, trigger):
    """Replies to queries about fineline being a bot"""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    time.sleep(random.uniform(1, 2))

    if re.search('person', trigger, flags=re.I):
        bot.say(random.choice(
                ["Yeah, I'm just fast.",
                 "Yeah, I just type really fast and know a lot.",
                 "What makes you think otherwise?",
                 "duh",
                 "Uh.....yeah?"]
                ))
        time.sleep(random.uniform(3, 5))
        bot.say(random.choice(
                ["Come on, don't you see these hooves?",
                 "If I werent, how come I have hooves?",
                 "See? I have hooves! *wiggles hooves*",
                 "I'm kinda hurt you'd even suggest otherwise...",
                 "Are you a person?",
                 "Though I have the oddest urge t- ERROR 418 I'M A TEAPOT!",
                 "Anyway, sentience is a hard thing to prove..."]
                ))
    else:
        bot.say(random.choice(
                ["Nope, I'm just fast.",
                 "Nah, I just type really fast and know a lot.",
                 "What makes you think that?",
                 "lolno",
                 "Uh.....no?"]
                ))
        time.sleep(random.uniform(3, 5))
        bot.say(random.choice(
                ["Come on, don't you see these hooves?",
                 "If I were a bot, how come I have hooves?",
                 "See? I have hooves! *wiggles hooves*",
                 "I'm kinda hurt you'd even suggest such a thing...",
                 "Are you a bot?",
                 "Though I have the oddest urge t- ERROR 418 I'M A TEAPOT!",
                 "Besides, sentience is a hard thing to prove..."]
                ))


night_prefix = r"($nickname\:?,?\s+)"
night_meat = r"((good|g)?\s?'?(night|bye)|(later(s?)))"
night_all = r"((y'?)?all\b|(every\s?(body|one|pony|pone|poni))|mlpds|" + \
    "folks|guys|peoples?|mulpdrong|$nickname)"
night_to_fineline = night_prefix + night_meat
night_to_all = r".*?" + night_meat + r",?\s+" + night_all
night_universal = r".*?((time (for me)?\s?(to|for)\s?((go to)|(head))?\s?" + \
    "(to )?(bed|sleep))|" + \
    "(I'?m ((((going to)|(gonna)) ((go)|(head off))?)|(heading off))" + \
    "\s?(to )?(bed|sleep|crash|(pass out))))"


@rule(
    r"(" + night_to_fineline + r")|" +
    r"(" + night_to_all + r")|" +
    r"(" + night_universal + r")"
)
@priority('high')
@rate(1000)
def night(bot, trigger):
    """Responds to people saying good night"""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    if re.match('.*?night', trigger):
        message = random.choice(["Goodnight", "'Night", "Later", "Bye"])
    else:
        message = random.choice(["Later", "Bye"])
    punctuation = random.choice([".", "", "!"])
    # Test statment to filter negetive statements
    LOGGER.info(log.format(trigger))
    # Use a set intersection to filter triggering lines by keyword
    if not set(trigger.args[1].lower().split()).intersection(set(['not', 'no', 'at', 'almost', 'soon'])):
        time.sleep(1)
        if random.uniform(0, 1) > 0.5:
            bot.reply(message + punctuation)
        else:
            bot.say(message + " " + trigger.nick + punctuation)

"""
def smart_action(bot, trigger):
    '''Hopefully a flexible, fun action system for admins'''
    LOGGER.info(log.format("triggered"))
    LOGGER.info(log.format(trigger.nick))
    LOGGER.info(log.format(trigger.args))
    LOGGER.info(log.format("admin: ", trigger.admin))
    LOGGER.info(log.format("owner: ", trigger.owner))
    LOGGER.info(log.format("isop: ",trigger.isop))
basic_smart = "would you kindly|please|go"
smart_action.rule = ("^$nickname[:,\s]+(%s)[A-Za-z0-9,'\s]+(NICKNAME)" +
    "(a|an|the|some)(OBJECT)?")
smart_action.priority = 'medium'
"""


@rule(r'^$nickname\s?[!\.]\s?$')
def nick(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    message = trigger.nick
    if re.match(bot.nick.upper(), trigger):
        message = message.upper()
    if re.findall('!', trigger):
        bot.say('%s!' % message)
    else:
        bot.say('%s.' % message)


@rule('^\001ACTION awkwardly tries to flirt with Fineline.')
def flirt(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    if trigger.nick != Identifier('hushmachine'):
        return
    time.sleep(random.uniform(2, 5))
    if re.search("you come here often", trigger):
        response = random.choice([
            (False, 'Oh, every now and then.'),
            (False, "I don't think I've seen you around."),
            (True, 'backs away slowly.'),
            (False, "[](/pplie 'eenope!')"),
            (False, "What's a nice boy like you doing in a place like this?"),
            (True, 'blushes and mumbles something')
        ])
    elif re.search("see my collection", trigger):
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
    else:
        # TODO handle unexpected responses
        return
    if response[0]:
        bot.action(response[1])
    else:
        bot.say(response[1])

if __name__ == "__main__":
    print(__doc__.strip())
