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
from types import *

RESET = "\x0f"
COLORS = {
        "white": "00",
        "black": "01",
        "dark blue": "02", "navy": "02",
        "green": "03",
        "red": "04",
        "dark red": "05", "brown": "05", "maroon": "05",
        "purple": "06", "violet": "06",
        "orange": "07", "olive": "07",
        "yellow": "08",
        "light green": "09", "lime": "09",
        "teal": "10", "blue cyan": "10",
        "cyan": "11", "aqua": "11",
        "blue": "12", "light blue": "12", "royal blue": "12",
        "magenta": "13", "pink": "13", "light red": "13", "fuchsia": "13",
        "dark grey": "14", "dark gray": "14", "grey": "14", "gray": "14",
        "light grey": "15", "light gray": "15", "silver": "15"
        }
STYLES = {
        "i": "\x16", "italic": "\x16",
        "u": "\x1F", "underline": "\x1F",
        "b": "\x02", "bold": "\x02"
        }

def colorize(text, colors=[], styles=[]):
    assert isinstance(text, basestring), "No string provided."
    assert text, "Text is empty."
    assert type(colors) is ListType, "Colors must be in a list."
    assert type(styles) is ListType, "Styles must be in a list."
    assert len(colors) < 3, "Too many colors."
    assert len(styles) < 4, "Too many styles."

    if colors or styles:
        message = u'%s' % text
        if len(colors) == 1:
            try:
                message = u'\x03%s%s%s' % (COLORS[colors[0].lower()], message, RESET)
            except KeyError:
                raise KeyError('Color "%s" is invalid.' % colors[0])
        elif len(colors) ==2:
            try:
                message = u'\x03%s,%s%s\x0f' % (
                        COLORS[colors[0].lower()],
                        COLORS[colors[1].lower()],
                        message
                        )
            except KeyError:
                raise KeyError('Color pair "%s, %s" is invalid.' % (
                    colors[0],
                    colors[1]
                    ))
        if styles:
            for style in styles:
                try:
                    message = u'%s%s\x0f' % (STYLES[style.lower()], message)
                except KeyError:
                    raise KeyError('Style "%s" is invalid.' % style)
        return message
    else:
        return text


def rainbow(text):
    assert isinstance(text, basestring), "No string provided."
    assert text, "Text is empty."
    rainbow = ['black', 'red', 'navy', 'green', 'purple', 'pink']
    message = u''
    for c in text:
        message = u'%s%s' % (
                message,
                colorize(c, [rainbow[choice(range(len(rainbow)))]])
                )
    message = u'%s%s' % (message, RESET)
    return message


if __name__ == "__main__":
    print __doc__.strip()
