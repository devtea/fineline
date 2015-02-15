"""
wolframalpha.py - A wolfram alpha query module
Copyright 2015, khyperia
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import re
import sys
from socket import timeout

if sys.version_info.major < 3:
    import HTMLParser
else:
    import html.parser as HTMLParser

from willie.module import commands, example
from willie import web


@commands('wa', 'wolfram', 'wolframalpha')
@example('!wolframalpha 2 + 2')
def wolframalpha(bot, trigger):
    if not trigger.group(2):
        return bot.reply("Usage: !wolframalpha [expression]")
    query = trigger.group(2)
    try:
        uri = 'http://tumbolia.appspot.com/wa/'
        query = web.quote(query.replace('+', 'plus'))
        answer = web.get(uri + query, 45, dont_decode=True)
    except timeout:
        return bot.say('WolframAlpha timed out')
    if not answer:
        return bot.reply('No answer')
    answer = answer.decode('unicode_escape')
    answer = HTMLParser.HTMLParser().unescape(answer)
    while True:
        match = re.search('\\\:([0-9A-Fa-f]{4})', answer)
        if match is None:
            break
        char_code = match.group(1)
        char = unichr(int(char_code, 16))
        answer = answer.replace('\:' + char_code, char)
    waOutputArray = answer.split(';')
    if(len(waOutputArray) < 2):
        if(answer.strip() == "Couldn't grab results from json stringified precioussss."):
            # Answer isn't given in an IRC-able format, just link to it.
            bot.say('Couldn\'t display answer, try http://www.wolframalpha.com/input/?i=' + query.replace(' ', '+'))
        else:
            bot.say('Wolfram error: ' + answer)
    else:
        bot.say(waOutputArray[0] + " = " + waOutputArray[1])


if __name__ == "__main__":
    print __doc__.strip()
