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

from willie.logger import get_logger
from willie.module import commands, example
import willie.web as web

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


def mlfw_search(bot, terms):
    base_url = u'http://mylittlefacewhen.com/api/v3/face/'
    query_strings = u'?removed=false&limit=1' + terms
    LOGGER.info(log.format(query_strings))
    try:
        result = web.get(base_url + query_strings, 10)
    except timeout:
        return False
    try:
        json_results = json.loads(result)
    except ValueError:
        LOGGER.warning(log.format(u"Bad json returned from mlfw"))
        LOGGER.warning(log.format(result))
    LOGGER.info(log.format(json.dumps(json_results, sort_keys=False, indent=2)))
    try:
        return json_results['objects'][0]['image']
    except IndexError:
        return None
    except TypeError:
        return False


@commands(u'mlfw')
@example(u"!mlfw tag one, tag two, tag three")
def mlfw(bot, trigger):
    """Searches the my little face when site and returns the top result from all the specified tags."""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    LOGGER.info(log.format(u"Triggered =============="))
    LOGGER.info(log.format(trigger.groups()[1]))
    list = trigger.groups()[1]
    if not list:
        bot.reply(u"try something like %s" % mlfw.example[0]['example'])
    else:
        LOGGER.info(log.format(list))
        args = list.split(u',')
        for i, str in enumerate(args):
            args[i] = quote(str.strip())
        LOGGER.info(log.format(args))
        tags = u'&tags__all=' + u','.join(args)
        LOGGER.info(log.format(tags))
        mlfw_result = mlfw_search(bot, tags)
        if mlfw_result:
            LOGGER.info(log.format(mlfw_result))
            bot.reply(u'http://mylittlefacewhen.com%s' % mlfw_result)
        elif mlfw_result is False:  # looks bad, but must since might be None
            bot.reply(u"Uh oh, MLFW isn't working right. Try again later.")
        else:
            bot.reply(u"That doesn't seem to exist.")


if __name__ == "__main__":
    print(__doc__.strip())
