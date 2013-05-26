"""
hugback.py - A simple Willie Module for replying to 'hug' actions
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

def hugback(Willie, trigger):
    """Returns a 'hug' action directed at the bot."""

    Willie.action('hugs %s back' % trigger.nick)
# Rules allow regex matches to PRIVMSG
hugback.rule = r'\001ACTION hugs $nickname'

# Priorities of 'high', 'medium', and 'low' work
hugback.priority = 'medium'

# Willie is multithreaded by default.
#hugback.thread = False

# Limit in seconds of users ability to trigger module
hugback.rate = 30



if __name__ == "__main__":
    print __doc__.strip()
