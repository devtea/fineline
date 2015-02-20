"""
mlfw.py - A simple Willie module to parse tags and return results from the
mlfw site
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import json
from urllib.parse import quote
from socket import timeout

from willie.logger import get_logger
from willie.module import commands, example
import willie.web as web

# Bot framework is stupid about importing, so we need to do silly stuff
try:
    import log
except:
    import sys
    import os.path
    sys.path.append(os.path.join('.', '.willie', 'modules'))
    import log
    if 'log' not in sys.modules:
        sys.modules['log'] = log

LOGGER = get_logger(__name__)


def mlfw_search(bot, terms):
    base_url = 'http://mylittlefacewhen.com/api/v3/face/'
    query_strings = '?removed=false&limit=1' + terms
    LOGGER.info(log.format(query_strings))
    try:
        result = web.get(base_url + query_strings, 10)
    except timeout:
        return False
    try:
        json_results = json.loads(result)
    except ValueError:
        LOGGER.warning(log.format("Bad json returned from mlfw"))
        LOGGER.warning(log.format(result))
    LOGGER.info(log.format(json.dumps(json_results, sort_keys=False, indent=2)))
    try:
        return json_results['objects'][0]['image']
    except IndexError:
        return None
    except TypeError:
        return False


@commands('mlfw')
@example("!mlfw tag one, tag two, tag three")
def mlfw(bot, trigger):
    """Searches the my little face when site and returns the top result from all the specified tags."""
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return
    LOGGER.info(log.format("Triggered =============="))
    LOGGER.info(log.format(trigger.groups()[1]))
    list = trigger.groups()[1]
    if not list:
        bot.reply("try something like %s" % mlfw.example[0]['example'])
    else:
        LOGGER.info(log.format(list))
        args = list.split(',')
        for i, str in enumerate(args):
            args[i] = quote(str.strip())
        LOGGER.info(log.format(args))
        tags = '&tags__all=' + ','.join(args)
        LOGGER.info(log.format(tags))
        mlfw_result = mlfw_search(bot, tags)
        if mlfw_result:
            LOGGER.info(log.format(mlfw_result))
            bot.reply('http://mylittlefacewhen.com%s' % mlfw_result)
        elif mlfw_result is False:  # looks bad, but must since might be None
            bot.reply("Uh oh, MLFW isn't working right. Try again later.")
        else:
            bot.reply("That doesn't seem to exist.")


if __name__ == "__main__":
    print(__doc__.strip())
