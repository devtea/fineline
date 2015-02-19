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
from willie.module import commands, example

RESET = "\x0f"
COLORS = {
    "white": "00", "0": "00", "00": "00",
    "black": "01", "1": "01", "01": "01",
    "dark blue": "02", "navy": "02", "2": "02", "02": "02",
    "green": "03", "3": "03", "03": "03",
    "red": "04", "4": "04", "04": "04",
    "dark red": "05", "brown": "05", "maroon": "05", "5": "05", "05": "05",
    "purple": "06", "violet": "06", "6": "06", "06": "06",
    "orange": "07", "olive": "07", "7": "07", "07": "07",
    "yellow": "08", "8": "08", "08": "08",
    "light green": "09", "lime": "09", "9": "09", "09": "09",
    "teal": "10", "blue cyan": "10", "10": "10",
    "cyan": "11", "aqua": "11", "11": "11",
    "blue": "12", "light blue": "12", "royal blue": "12", "12": "12",
    "magenta": "13", "pink": "13", "light red": "13", "fuchsia": "13", "13": "13",
    "dark grey": "14", "dark gray": "14", "grey": "14", "gray": "14", "14": "14",
    "light grey": "15", "light gray": "15", "silver": "15", "15": "15"
}
STYLES = {
    "i": "\x16", "italic": "\x16",
    "u": "\x1F", "underline": "\x1F",
    "b": "\x02", "bold": "\x02"
}


def colorize(text, colors=[], styles=[]):
    assert isinstance(text, str), "No string provided."
    assert text, "Text is empty."
    assert isinstance(colors, list), "Colors must be in a list."
    assert isinstance(styles, list), "Styles must be in a list."
    assert len(colors) < 3, "Too many colors."
    assert len(styles) < 4, "Too many styles."
    if colors or styles:
        message = text
        if len(colors) == 1:
            try:
                message = '\x03%s%s%s' % (COLORS[colors[0].lower()], message, RESET)
            except KeyError:
                raise KeyError('Color "%s" is invalid.' % colors[0])
            except UnicodeDecodeError:
                message = message
                message = '\x03%s%s%s' % (COLORS[colors[0].lower()], message, RESET)
        elif len(colors) == 2:
            try:
                message = '\x03%s,%s%s\x0f' % (
                    COLORS[colors[0].lower()],
                    COLORS[colors[1].lower()],
                    message
                )
            except KeyError:
                raise KeyError('Color pair "%s, %s" is invalid.' % (
                    colors[0],
                    colors[1]
                ))
            except UnicodeDecodeError:
                message = message
                message = '\x03%s,%s%s\x0f' % (
                    COLORS[colors[0].lower()],
                    COLORS[colors[1].lower()],
                    message
                )
        if styles:
            for style in styles:
                try:
                    message = '%s%s\x0f' % (STYLES[style.lower()], message)
                except KeyError:
                    raise KeyError('Style "%s" is invalid.' % style)
                except UnicodeDecodeError:
                    message = message
                    message = '%s%s\x0f' % (STYLES[style.lower()], message)
        return message
    else:
        return text


def rainbow(text):
    assert isinstance(text, str), "No string provided."
    assert text, "Text is empty."
    rainbow = ['green', 'red', 'dark red', 'purple', 'orange', 'teal', 'magenta']
    message = ''
    for c in text:
            message = '%s%s' % (message, colorize(c, [rainbow[choice(range(len(rainbow)))]]))
    message = '%s%s' % (message, RESET)
    return message


@commands('rainbow')
@example('!rainbow rainbow trout')
def rb(bot, trigger):
    '''Colors text in a rainbow of fabulosity. Admin only.'''
    if not trigger.owner:
        return
    bot.say(rainbow(trigger[9:]))


@commands('colors')
def colors(bot, trigger):
    '''Prints out examples of most colors available in IRC. Admin only.'''
    if not trigger.owner:
        return
    for c in ['white', 'black', 'dark blue', 'green', 'red', 'dark red', 'purple',
              'orange', 'yellow', 'light green', 'teal', 'cyan', 'blue', 'magenta',
              'dark grey', 'light grey']:
        bot.say("%s %s %s %s" % (
            colorize(c, [c]),
            colorize('italic', [c], ['i']),
            colorize('bold', [c], ['b']),
            colorize('underline', [c], ['u'])
        ))


if __name__ == "__main__":
    print(__doc__.strip())
