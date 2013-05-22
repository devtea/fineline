"""
hugback.py - A simple Willie Module for replying to 'hug' actions
Copyright 2013, Tim Dreyer
Licensed under the Eiffel Forum License 2.

http://bitbucket.org/tdreyer/fineline
"""

def hugback(Willie, trigger):
    """Returns a 'hug' action directed at the bot."""
    Willie.action('hugs %s back' % trigger.nick)

hugback.rule = r'\001ACTION hugs $nickname'
hugback.priority = 'medium'
hugback.thread = False
hugback.rate = 30
#hugback.example = "Why don't you hug me and find out?!"

if __name__ == "__main__":
    print __doc__.strip()
