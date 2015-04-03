"""
dice.py - A dice rolling willie module.
Copyright 2015, khyperia, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

from willie.module import commands
import random


class DiceError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


# Note: Does not handle spaces. Strip all spaces from input.
def do_dice(string):
    index = 0

    def primary():
        nonlocal index
        if index < len(string) and string[index] == "(":
            index += 1
            prim_parse = parse(primary(), 0)
            if index >= len(string) or string[index] != ")":
                raise DiceError("Missing ')'")
            index += 1
            return prim_parse
        start_index = index
        while index < len(string) and string[index].isdigit():
            index += 1
        if index == start_index:
            raise DiceError("No digit where there should have been.")
        return int(string[start_index:index])

    def roll(x, y):
        if x > 1000:
            raise DiceError("Nobody has that many dice!")
        return sum((random.randint(1, int(y)) for i in range(0, int(x))))

    # add *one character* operators in this.
    # first number is precedence, second lambda is definition
    operators = {
        "+": (1, lambda x, y: x + y),
        "-": (1, lambda x, y: x - y),
        "*": (2, lambda x, y: x * y),
        "/": (2, lambda x, y: x / y),
        "%": (2, lambda x, y: x % y),
        "^": (3, lambda x, y: x ** y),
        "d": (4, lambda x, y: roll(x, y))
    }

    # http://en.wikipedia.org/wiki/Operator-precedence_parser
    def parse(lhs, min_precedence):
        nonlocal index
        while index < len(string) and string[index] in operators and operators[string[index]][0] >= min_precedence:
            op = string[index]
            index += 1
            rhs = primary()
            while index < len(string) and string[index] in operators and operators[string[index]][0] > operators[op][0]:
                rhs = parse(rhs, operators[string[index]][0])
            lhs = operators[op][1](lhs, rhs)
        return lhs

    result = parse(primary(), 0)
    if index != len(string):
        raise DiceError("Couldn't parse string")
    return result


def general_dice(string):
    # Special case if words just contains an integer
    try:
        return "Your roll is: " + str(random.randint(1, int(string)))
    except ValueError:
        pass

    try:
        return "Your roll is: " + str(do_dice(string))
    except DiceError as e:
        return "Uh oh! " + str(e)


@commands(u'dice')
def dice(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    # Take out command and strip spaces from rest
    words = ''.join(trigger.args[1].split(' ')[1:])
    bot.say(general_dice(words))

