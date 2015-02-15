'''
A utility to aid bot plugins.
provides a more customized logging format
'''
import time


def format(*args):
    message = ''.join([i for i in args])
    return '%s - %s' % (time.strftime("%Y-%m-%d %H:%M:%S"), message)
'''
Usage examples:

from willie.logger import get_logger

LOGGER = get_logger(__name__)

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    import os.path
    try:
        LOGGER.info("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', [os.path.join('.', '.willie', 'modules')])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()

logger.info(log.format(text))

'''
