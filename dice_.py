"""
dice.py - A dice rolling willie module.
Copyright 2015, khyperia, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

from willie.module import commands
import random

random.seed()


def roll(num_dice, sides_dice):
    rolls = []
    if num_dice < 1 or sides_dice <= 1:
        return "I can't roll those dice"
    if num_dice > 100:
        return "Don't roll more than 100 dice"
    for x in range(0, num_dice):
        rolls.append(random.randrange(1, sides_dice))
    if len(rolls) == 1:
        return "Your {} sided dice roll is: {}".format(sides_dice, rolls[0])
    rolls_str = [str(r) for r in rolls]
    return "Your {}d{} roll is: {} = {}".format(num_dice, sides_dice, ' + '.join(rolls_str), sum(rolls))


def roll_d_str(value):
    d_split = value.split('d')
    try:
        if len(d_split) == 1:
            sides_dice = int(d_split[0])
            return roll(1, sides_dice)
        elif len(d_split) == 2:
            num_dice = int(d_split[0])
            sides_dice = int(d_split[1])
            return roll(num_dice, sides_dice)
    except ValueError:
        return "Those aren't numbers, silly"


def roll_two_str(first, second):
    try:
        fst = int(first)
        snd = int(second)
        return roll(fst, snd)
    except ValueError:
        return "Those aren't numbers, silly"


@commands(u'dice')
def dice(bot, trigger):
    # Don't do anything if the bot has been shushed
    if bot.memory['shush']:
        return

    words = trigger.args[1].split(' ')
    if len(words) == 1:
        bot.reply(roll_d_str(words[0]))
    elif len(words) == 2:
        bot.reply(roll_two_str(words[0], words[1]))
    else:
        bot.reply("Usage: !dice [number of dice]d[number of sides on dice]")
