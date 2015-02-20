'''
A utility to aid bot plugins.
provides a more customized logging format
'''
import time


def format(*args):
    message = ''.join([str(i) for i in args])
    return '%s - %s' % (time.strftime("%Y-%m-%d %H:%M:%S"), message)
'''
Usage examples:

from willie.logger import get_logger

LOGGER = get_logger(__name__)

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

logger.info(log.format(text))

'''
