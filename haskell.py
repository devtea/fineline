"""
haskell.py - A module for using mueval (Haskell eval) interactively
Copyright 2014, khyperia
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline

Required setup (on Arch):
pacman -S ghc cabal-install && cabal install quickcheck mueval
Add ~/.cabal/bin to $PATH so it is accessible from python's subprocess.check_output
(for example, adding "export PATH=$HOME/.cabal/bin:$PATH" to ~/.bashrc and logging out/in)

"""
from __future__ import print_function

from willie.module import commands
import subprocess

MAX_CHARS = 100


def stopspam(value):
    # trim up the result to stop spam
    value = value.replace('\r', ' ').replace('\n', ' ')
    if len(value) > MAX_CHARS:
        value = value[:MAX_CHARS] + "..."
    return value


# this is really kind of unnecessary, could just
# return ' '.join(arglist.split(' ')[1:])
# but I (khyperia) like my RankNTypes option :3
def getargs(arglist):
    split = arglist.split(' ')[1:]
    args = []
    while len(split) > 0:
        argtype = split[0]
        if argtype == '-X' and len(split) > 1:  # language extension
            args += [split[0], split[1]]
            split = split[2:]
        elif argtype == '-i':  # show type as well as expression
            args += [split[0]]
            split = split[1:]
        else:
            break  # disallowed option (potentially dangerous)
    return args, ' '.join(split)


@commands(u'haskell', u'h')
def haskell(bot, trigger):
    args, expression = getargs(trigger.args[1])

    if len(expression) == 0:
        bot.say("Usage: haskell [expression]")
        return

    try:
        result = subprocess.check_output(['mueval-core'] + args + ['--expression', expression])
    except subprocess.CalledProcessError as err:
        result = "Error: " + err.output

    result = stopspam(result)
    bot.say(result)


if __name__ == "__main__":
    print(__doc__.strip())
