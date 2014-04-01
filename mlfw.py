"""
mlfw.py - A simple Willie module to parse tags and return results from the
mlfw site
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
from __future__ import print_function

import json
from urllib import quote
from socket import timeout

import willie.web as web
from willie.module import commands, example

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


def mlfw_search(bot, terms):
    base_url = u'http://mylittlefacewhen.com/api/v3/face/'
    query_strings = u'?removed=false&limit=1' + terms
    bot.debug(__file__, log.format(query_strings), u"verbose")
    try:
        result = web.get(base_url + query_strings, 10)
    except timeout:
        return False
    try:
        json_results = json.loads(result)
    except ValueError:
        bot.debug(__file__, log.format(u"Bad json returned"), u"warning")
        bot.debug(__file__, log.format(result), u"warning")
    bot.debug(__file__,
              log.format(json.dumps(json_results, sort_keys=False, indent=2)),
              u"verbose")
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
    bot.debug(__file__, log.format(u"Triggered =============="), u"verbose")
    bot.debug(__file__, log.format(trigger.groups()[1]), u"verbose")
    list = trigger.groups()[1]
    if not list:
        bot.reply(u"try something like %s" % mlfw.example[0]['example'])
    else:
        bot.debug(__file__, log.format(list), u"verbose")
        args = list.split(u',')
        for i, str in enumerate(args):
            args[i] = quote(str.strip())
        bot.debug(__file__, log.format(args), u"verbose")
        tags = u'&tags__all=' + u','.join(args)
        bot.debug(__file__, log.format(tags), u"verbose")
        mlfw_result = mlfw_search(bot, tags)
        if mlfw_result:
            bot.debug(__file__, log.format(mlfw_result), u"verbose")
            bot.reply(u'http://mylittlefacewhen.com%s' % mlfw_result)
        elif mlfw_result is False:  # looks bad, but must since might be None
            bot.reply(u"Uh oh, MLFW isn't working right. Try again later.")
        else:
            bot.reply(u"That doesn't seem to exist.")


if __name__ == "__main__":
    print(__doc__.strip())
