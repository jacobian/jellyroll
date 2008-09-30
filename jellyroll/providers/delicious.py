import time
import dateutil.parser
import dateutil.tz
import logging
import urllib
from django.conf import settings
from django.db import transaction
from django.utils.encoding import smart_unicode
from jellyroll.models import Item, Bookmark
from jellyroll.providers import utils

#
# Super-mini Delicious API
#
class DeliciousClient(object):
    """
    A super-minimal delicious client :)
    """
    
    lastcall = 0
    
    def __init__(self, username, password, method='v1'):
        self.username, self.password = username, password
        self.method = method
        
    def __getattr__(self, method):
        return DeliciousClient(self.username, self.password, '%s/%s' % (self.method, method))
        
    def __repr__(self):
        return "<DeliciousClient: %s>" % self.method
        
    def __call__(self, **params):
        # Enforce Yahoo's "no calls quicker than every 1 second" rule
        delta = time.time() - DeliciousClient.lastcall
        if delta < 2:
            time.sleep(2 - delta)
        DeliciousClient.lastcall = time.time()
        url = ("https://api.del.icio.us/%s?" % self.method) + urllib.urlencode(params)        
        return utils.getxml(url, username=self.username, password=self.password)

#
# Public API
#

log = logging.getLogger("jellyroll.providers.delicious")

def enabled():
    return hasattr(settings, 'DELICIOUS_USERNAME') and hasattr(settings, 'DELICIOUS_PASSWORD')
    
def update():
    delicious = DeliciousClient(settings.DELICIOUS_USERNAME, settings.DELICIOUS_PASSWORD)

    # Check to see if we need an update
    last_update_date = Item.objects.get_last_update_of_model(Bookmark)
    last_post_date = utils.parsedate(delicious.posts.update().get("time"))
    if last_post_date <= last_update_date:
        log.info("Skipping update: last update date: %s; last post date: %s", last_update_date, last_post_date)
        return

    for datenode in reversed(list(delicious.posts.dates().getiterator('date'))):
        dt = utils.parsedate(datenode.get("date"))
        if dt > last_update_date:
            _update_bookmarks_from_date(delicious, dt)
                
#
# Private API
#

def _update_bookmarks_from_date(delicious, dt):
    log.debug("Reading bookmarks from %s", dt)
    xml = delicious.posts.get(dt=dt.strftime("%Y-%m-%d"))
    for post in xml.getiterator('post'):
        info = dict((k, smart_unicode(post.get(k))) for k in post.keys())
        log.debug("Handling bookmark of %r", info["href"])
        _handle_bookmark(info)
_update_bookmarks_from_date = transaction.commit_on_success(_update_bookmarks_from_date)

def _handle_bookmark(info):
    b, created = Bookmark.objects.get_or_create(
        url         = info['href'],
        defaults = dict(
            description = info['description'],
            extended    = info.get('extended', ''),
        )
    )
    if not created:
        b.description = info['description']
        b.extended = info.get('extended', '')
        b.save()
    return Item.objects.create_or_update(
        instance = b, 
        timestamp = utils.parsedate(info['time']), 
        tags = info.get('tag', ''),
        source = __name__,
        source_id = info['hash'],
    )

