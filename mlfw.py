"""
mlfw.py - A simple Willie module to parse tags and return results from the
mlfw site
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import json
from urllib import quote
from socket import timeout

import willie.web as web
from willie.module import commands, example


def mlfw_search(bot, terms):
    base_url = u'http://mylittlefacewhen.com/api/v3/face/'
    query_strings = u'?removed=false&limit=1' + terms
    bot.debug(u"mlfw.py:mlfw_search", query_strings, u"verbose")
    try:
        result = web.get(base_url + query_strings, 10)
    except timeout:
        return False
    try:
        json_results = json.loads(result)
    except ValueError:
        bot.debug(u"mlfw.py:mlfw_search", u"Bad json returned", u"warning")
        bot.debug(u"mlfw.py:mlfw_search", result, u"warning")
    bot.debug(u"mlfw.py:mlfw_search",
              json.dumps(json_results, sort_keys=False, indent=2),
              u"verbose"
              )
    try:
        return json_results['objects'][0]['image']
    except IndexError:
        return None
    except TypeError:
        return False


@commands(u'mlfw')
@example(u"!mlfw tag one, tag two, tag three")
def mlfw(bot, trigger):
    """Searches mlfw and returns the top result with all tags specified."""
    bot.debug(u"mlfw.py:mlfw", u"Triggered ==============", u"verbose")
    bot.debug(u"mlfw.py:mlfw", trigger.groups()[1], u"verbose")
    list = trigger.groups()[1]
    if not list:
        bot.reply(u"try something like %s" % mlfw.example[0]['example'])
    else:
        bot.debug(u"mlfw.py:mlfw", list, u"verbose")
        args = list.split(u',')
        for i, str in enumerate(args):
            args[i] = quote(str.strip())
        bot.debug(u"mlfw.py:mlfw", args, u"verbose")
        tags = u'&tags__all=' + u','.join(args)
        bot.debug(u"mlfw.py:mlfw", tags, u"verbose")
        mlfw_result = mlfw_search(bot, tags)
        if mlfw_result:
            bot.debug(u"mlfw.py:mlfw", mlfw_result, u"verbose")
            bot.reply(u'http://mylittlefacewhen.com%s' % mlfw_result)
        elif mlfw_result is False:  # looks bad, but must since might be None
            bot.reply(u"Uh oh, MLFW isn't working right. Try again later.")
        else:
            bot.reply(u"That doesn't seem to exist.")


if __name__ == "__main__":
    print __doc__.strip()
