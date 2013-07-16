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
from willie.module import commands, example


def mlfw_search(Willie, terms):
    base_url = u'http://mylittlefacewhen.com/api/v3/face/'
    query_strings = u'?removed=false&limit=1' + terms
    Willie.debug(u"mlfw.py:mlfw_search", query_strings, u"verbose")
    result = web.get(base_url + query_strings, 10)
    try:
        json_results = json.loads(result)
    except ValueError:
        Willie.debug(u"mlfw.py:mlfw_search", u"Bad json returned", u"warning")
        Willie.debug(u"mlfw.py:mlfw_search", result, u"warning")
    Willie.debug(u"mlfw.py:mlfw_search",
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
def mlfw(Willie, trigger):
    """Searches mlfw and returns the top result with all tags specified."""
    Willie.debug(u"mlfw.py:mlfw", u"Triggered ==============", u"verbose")
    Willie.debug(u"mlfw.py:mlfw", trigger.groups()[1], u"verbose")
    list = trigger.groups()[1]
    if not list:
        Willie.reply(u"try something like %" % mlfw.example)
    else:
        Willie.debug(u"mlfw.py:mlfw", list, u"verbose")
        args = list.split(u',')
        for i, str in enumerate(args):
            args[i] = quote(str.strip())
        Willie.debug(u"mlfw.py:mlfw", args, u"verbose")
        tags = u'&tags__all=' + u','.join(args)
        Willie.debug(u"mlfw.py:mlfw", tags, u"verbose")
        mlfw_result = mlfw_search(Willie, tags)
        if mlfw_result:
            Willie.debug(u"mlfw.py:mlfw", mlfw_result, u"verbose")
            Willie.reply(u'http://mylittlefacewhen.com%s' % mlfw_result)
        elif mlfw_result is False:  # looks bad, but must since might be None
            Willie.reply(u"Uh oh, MLFW isn't working right. Try again later.")
        else:
            Willie.reply(u"That doesn't seem to exist.")


if __name__ == "__main__":
    print __doc__.strip()
