"""
ponytime.py - grabs the next episode from a published api and spits out time til airing
Copyright 2014, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""
import re
import requests

from datetime import datetime, timedelta

from willie.logger import get_logger
from willie.module import commands, rate

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


def dtformat(timedelta):
    days = timedelta.days
    hours, rem = divmod(timedelta.seconds, 3600)
    min, sec = divmod(rem, 60)

    if days == 0:
        d = ''
    elif days == 1:
        d = '1 day'
    else:
        d = '%i days' % days

    if hours == 0:
        h = ''
    elif hours == 1:
        h = '1 hour'
    else:
        h = '%i hours' % hours

    if min == 0:
        m = ''
    elif min == 1:
        m = '1 minute'
    else:
        m = '%i minutes' % min

    if sec == 0:
        s = ''
    elif sec == 1:
        s = '1 second'
    else:
        s = '%i seconds' % sec

    elements = [i for i in [d, h, m, s] if i]
    if not elements:
        return None
    if len(elements) == 1:
        return elements[0]
    return ' and '.join([', '.join(elements[0:-1]), elements[-1]])


@commands('ponytime')
@rate(90)
def ponytime(bot, trigger):
    """Grabs the latest episode times from ponycountdown.net and displays the time till the next episode"""
    LOGGER.info(log.format('Module called'))

    episode_list = re.compile('ponycountdowndates\[\d+\]=\[new Date\("([^"]+)"\),(\d+),(\d+),"([^"]+)"\];')
    js = requests.get("http://ponycountdown.com/api.js")

    results = episode_list.findall(js.content.decode('ascii'))

    # date_object = datetime.strptime(results[-1][0], '%B %d, %Y %H:%M:%S')
    dates = [(datetime.strptime(i[0], '%B %d, %Y %H:%M:%S'), i[1], i[2], i[3]) for i in results]
    # sorted_dates = sorted(dates, key = lambda x : (int(x[1]), int(x[2])))
    dates = sorted(dates, key=lambda x: x[0])

    now = datetime.utcnow()
    upcoming = [i for i in dates if i[0] > now - timedelta(seconds=1800)]
    if not upcoming:
        bot.say("I don't know when the next episode will be")
        return

    ep = upcoming[0]
    if ep[0] < now:  # if the episode has already started
        diff = now - ep[0]
        time = dtformat(diff)
        bot.say("This week's episode (%sx%s) started %s ago" % (ep[1], ep[2], time))
    elif ep[0] == now:
        bot.say("It's starting right now!!!!1one~")
    else:
        diff = ep[0] - now
        time = dtformat(diff)
        bot.say('Season %s, episode %s starts in %s' % (ep[1], ep[2], time))


if __name__ == "__main__":
    print(__doc__.strip())
