'''
A utility to aid bot plugins.
provides a more customized logging format
'''
import time


def format(*args):
    message = u''.join([unicode(i) for i in args])
    return u'%s - %s' % (time.strftime("%Y-%m-%d %H:%M:%S"), unicode(message))
'''
Usage examples:

from __future__ import print_function

# Bot framework is stupid about importing, so we need to override so that
# various modules are always available for import.
try:
    import log
except:
    import imp
    import sys
    try:
        print("Trying manual import of log formatter.")
        fp, pathname, description = imp.find_module('log', ['./.willie/modules/'])
        log = imp.load_source('log', pathname, fp)
        sys.modules['log'] = log
    finally:
        if fp:
            fp.close()

bot.debug(__file__, log.format(text), u'verbose')

'''
