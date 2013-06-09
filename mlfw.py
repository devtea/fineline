"""
mlfw.py - A simple Willie module to parse tags and return results from the
mlfw site
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import json
from urllib import quote

import willie.web as web


def mlfw_search(Willie, terms):
    base_url = 'http://mylittlefacewhen.com/api/v3/face/'
    query_strings = '?removed=false&limit=1' + terms
    Willie.debug("mlfw.py:mlfw_search", query_strings, "verbose")
    result = web.get(base_url + query_strings, 10)
    try:
        json_results = json.loads(result)
    except ValueError:
        Willie.debug("mlfw.py:mlfw_search", "Bad json returned", "warning")
        Willie.debug("mlfw.py:mlfw_search", result, "warning")
    Willie.debug(
            "mlfw.py:mlfw_search",
            json.dumps(json_results, sort_keys=False, indent=2),
            "verbose"
            )
    try:
        return json_results['objects'][0]['image']
    except IndexError:
        return None
    except TypeError:
        return False


def mlfw(Willie, trigger):
    """Searches mlfw and returns the top result with all tags specified."""
    Willie.debug("mlfw.py:mlfw", "Triggered ==============", "verbose")
    Willie.debug("mlfw.py:mlfw",trigger.groups()[1], "verbose")
    list = trigger.groups()[1]
    if not list:
        Willie.reply("try something like " + mlfw.example)
    else:
        Willie.debug("mlfw.py:mlfw", list, "verbose")
        args = list.split(',')
        for i, str in enumerate(args):
            args[i] = quote(str.strip())
        Willie.debug("mlfw.py:mlfw", args, "verbose")
        tags = '&tags__all=' + ','.join(args)
        Willie.debug("mlfw.py:mlfw", tags, "verbose")
        mlfw_result = mlfw_search(Willie, tags)
        if mlfw_result:
            Willie.debug("mlfw.py:mlfw", mlfw_result, "verbose")
            Willie.reply('http://mylittlefacewhen.com%s' % mlfw_result)
        elif mlfw_result is False:  #looks bad, but must since might be None
            Willie.reply("Uh oh, MLFW isn't working right. Try again later.")
        else:
            Willie.reply("That doesn't seem to exist.")
mlfw.commands = ['mlfw']
mlfw.rate = 45
mlfw.example = "!mlfw tag one, tag two, tag three"


if __name__ == "__main__":
    print __doc__.strip()
