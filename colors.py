'''
A utility to aid bot plugins.
Accepts strings and a color code, returns a string formatted with the
requested IRC color codes.

Recognized 'default' colors:
    00 White
    01 Black
    02 Dark blue
    03 Green
    04 Red
    05 Dark Red
    06 Purple
    07 Orange
    08 Yellow
    09 Light Green
    10 Teal
    11 Cyan
    12 Blue
    13 Magenta
    14 Dark Grey
    15 Light Grey
'''
from random import choice
from types import ListType
from willie.module import commands

RESET = u"\x0f"
COLORS = {
    u"white": u"00", u"0": u"00", u"00": u"00",
    u"black": u"01", u"1": u"01", u"01": u"01",
    u"dark blue": u"02", u"navy": u"02", u"2": u"02", u"02": u"02",
    u"green": u"03", u"3": u"03", u"03": u"03",
    u"red": u"04", u"4": u"04", u"04": u"04",
    u"dark red": u"05", u"brown": u"05", u"maroon": u"05", u"5": u"05", u"05": u"05",
    u"purple": u"06", u"violet": u"06", u"6": u"06", u"06": u"06",
    u"orange": u"07", u"olive": u"07", u"7": u"07", u"07": u"07",
    u"yellow": u"08", u"8": u"08", u"08": u"08",
    u"light green": u"09", u"lime": u"09", u"9": u"09", u"09": u"09",
    u"teal": u"10", u"blue cyan": u"10", u"10": u"10",
    u"cyan": u"11", u"aqua": u"11", u"11": u"11",
    u"blue": u"12", u"light blue": u"12", u"royal blue": u"12", u"12": u"12",
    u"magenta": u"13", u"pink": u"13", u"light red": u"13", u"fuchsia": u"13", u"13": u"13",
    u"dark grey": u"14", u"dark gray": u"14", u"grey": u"14", u"gray": u"14", u"14": u"14",
    u"light grey": u"15", u"light gray": u"15", u"silver": u"15", u"15": u"15"
}
STYLES = {
    u"i": "\x16", u"italic": "\x16",
    u"u": "\x1F", u"underline": "\x1F",
    u"b": "\x02", u"bold": "\x02"
}


def colorize(text, colors=[], styles=[]):
    assert isinstance(text, basestring), u"No string provided."
    assert text, u"Text is empty."
    assert type(colors) is ListType, u"Colors must be in a list."
    assert type(styles) is ListType, u"Styles must be in a list."
    assert len(colors) < 3, u"Too many colors."
    assert len(styles) < 4, u"Too many styles."
    if colors or styles:
        message = text
        if len(colors) == 1:
            try:
                message = u'\x03%s%s%s' % (COLORS[colors[0].lower()], message, RESET)
            except KeyError:
                raise KeyError(u'Color "%s" is invalid.' % colors[0])
            except UnicodeDecodeError:
                message = message.decode('utf-8', 'replace')
                message = u'\x03%s%s%s' % (COLORS[colors[0].lower()], message, RESET)
        elif len(colors) == 2:
            try:
                message = u'\x03%s,%s%s\x0f' % (
                    COLORS[colors[0].lower()],
                    COLORS[colors[1].lower()],
                    message
                )
            except KeyError:
                raise KeyError(u'Color pair "%s, %s" is invalid.' % (
                    colors[0],
                    colors[1]
                ))
            except UnicodeDecodeError:
                message = message.decode('utf-8', 'replace')
                message = u'\x03%s,%s%s\x0f' % (
                    COLORS[colors[0].lower()],
                    COLORS[colors[1].lower()],
                    message
                )
        if styles:
            for style in styles:
                try:
                    message = u'%s%s\x0f' % (STYLES[style.lower()], message)
                except KeyError:
                    raise KeyError(u'Style "%s" is invalid.' % style)
                except UnicodeDecodeError:
                    message = message.decode('utf-8', 'replace')
                    message = u'%s%s\x0f' % (STYLES[style.lower()], message)
        return message
    else:
        return text


def rainbow(text):
    assert isinstance(text, basestring), u"No string provided."
    assert text, u"Text is empty."
    rainbow = [u'green', u'red', u'dark red', u'purple', u'orange', u'teal', u'magenta']
    message = u''
    for c in text:
            message = u'%s%s' % (message, colorize(c, [rainbow[choice(range(len(rainbow)))]]))
    message = u'%s%s' % (message, RESET)
    return message


@commands('rainbow')
def rb(bot, trigger):
    if not trigger.owner:
        return
    bot.say(rainbow(trigger.bytes[9:]))


@commands('colors')
def colors(bot, trigger):
    if not trigger.owner:
        return
    for c in [u'white', u'black', u'dark blue', u'green', u'red', u'dark red', u'purple',
              u'orange', u'yellow', u'light green', u'teal', u'cyan', u'blue', u'magenta',
              u'dark grey', u'light grey']:
        bot.say(u"%s %s %s %s" % (
            colorize(c, [c]),
            colorize('italic', [c], ['i']),
            colorize('bold', [c], ['b']),
            colorize('underline', [c], ['u'])
        ))


if __name__ == "__main__":
    print __doc__.strip()
