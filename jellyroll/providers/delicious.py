import dateutil.parser
import dateutil.tz
import logging
import urllib
import itertools
from django.conf import settings
from django.db import transaction
from jellyroll.models import Item, Bookmark
from jellyroll.providers import utils

#
# Super-mini Delicious API
#
class DeliciousClient(object):
    """
    A super-minimal delicious client :)
    """
    def __init__(self, username, password, method='v1'):
        self.username, self.password = username, password
        self.method = method
        
    def __getattr__(self, method):
        return DeliciousClient(self.username, self.password, '%s/%s' % (self.method, method))
        
    def __repr__(self):
        return "<DeliciousClient: %s>" % self.method
        
    def __call__(self, **params):
        url = ("https://api.del.icio.us/%s?" % self.method) + urllib.urlencode(params)
        return utils.getxml(url, username=self.username, password=self.password)

#
# Public API
#

log = logging.getLogger("jellyroll.providers.delicious")

def enabled():
    return hasattr(settings, 'DELICIOUS_USERNAME') and hasattr(settings, 'DELICIOUS_PASSWORD')

def needs_update():
    last_update_date = Item.objects.get_last_update_of_model(Bookmark)
    log.debug("Last update date: %s", last_update_date)
    
    delicious = DeliciousClient(settings.DELICIOUS_USERNAME, settings.DELICIOUS_PASSWORD)
    last_post_date = utils.parsedate(delicious.posts.update().get("time"))
    log.debug("Last delicious post date: %s", last_post_date)

    return last_post_date > last_update_date
    
def update():
    last_update_date = Item.objects.get_last_update_of_model(Bookmark)
    delicious = DeliciousClient(settings.DELICIOUS_USERNAME, settings.DELICIOUS_PASSWORD)
    for datenode in reversed(list(delicious.posts.dates().getiterator('date'))):
        dt = utils.parsedate(datenode.get("date"))
        if dt > last_update_date:
            log.debug("Reading bookmarks from %s", dt)
            xml = delicious.posts.get(dt=dt.strftime("%Y-%m-%d"))
            for post in xml.getiterator('post'):
                info = dict((k, utils.safestr(post.get(k))) for k in post.keys())
                log.debug("Handling bookmark of %r", info["href"])
                _handle_bookmark(info)
                
#
# Private API
#

@transaction.commit_on_success      
def _handle_bookmark(info):
    b = Bookmark(
        url         = info['href'],
        description = info['description'],
        extended    = info.get('extended', ''),
    )
    return Item.objects.create_or_update(
        instance = b, 
        timestamp = utils.parsedate(info['time']), 
        tags = info.get('tag', ''),
        source = __name__,
        source_id = info['hash'],
    )

