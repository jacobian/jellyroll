import logging
import urllib
from django.conf import settings
from django.utils.encoding import smart_unicode
from jellyroll.models import Item, Bookmark
from jellyroll.providers import utils

#
# Magnolia client, contributed by Rob Hudson
#
class MagnoliaClient(object):
    """
    A super-minimal Magnolia client :)
    """
    def __init__(self, api_key, method=None):
        self.api_key = api_key
        self.method = method
        
    def __getattr__(self, method):
        return MagnoliaClient(self.api_key, method)
        
    def __repr__(self):
        return "<MagnoliaClient: %s>" % self.method
        
    def __call__(self, **params):
        params['api_key'] = self.api_key
        url = ("http://ma.gnolia.com/api/rest/1/%s/?" % (self.method)) + urllib.urlencode(params)
        return utils.getxml(url)

#
# Public API
#

log = logging.getLogger("jellyroll.providers.magnolia")

def enabled():
    ok = hasattr(settings, 'MAGNOLIA_API_KEY') and hasattr(settings, 'MAGNOLIA_USERNAME')
    if not ok:
        log.warn('The Magnolia provider is not available because the '
                 'MAGNOLIA_API_KEY and/or MAGNOLIA_USERNAME settings are '
                 'undefined.')
    return ok
    
def update():
    magnolia = MagnoliaClient(settings.MAGNOLIA_API_KEY)

    # Check to see if we need an update
    last_update_date = Item.objects.get_last_update_of_model(Bookmark)
    params = {'person': settings.MAGNOLIA_USERNAME}
    if last_update_date:
        params['from'] = last_update_date.isoformat()
    xml = magnolia.bookmarks_find(**params)
    _update_bookmarks(xml)
                
#
# Private API
#

def _update_bookmarks(xml):
    for bookmark in xml.getiterator('bookmark'):
        # Get attribute belonging to the bookmark element
        info = dict((k, smart_unicode(bookmark.get(k))) for k in bookmark.keys())
        # Handle child tags under the bookmark element
        for e in bookmark.getchildren():
            if e.tag == 'tags':
                info['tags'] = ' '.join([t.get('name') for t in e.getchildren()])
            else:
                info[e.tag] = e.text
        _handle_bookmark(info)
        
def _handle_bookmark(info):
    """
    info.keys() ==> ['id', 'created', 'updated', 'rating', 'private', 'owner', 
                     'title', 'url', 'description', 'screenshot', 'tags']
    Current Bookmark model doesn't support all of these.
    """
    if info['private'] == 'false':
        b, created = Bookmark.objects.get_or_create(
            url = info['url'],
            defaults = dict(
                description = info['title'],
                extended = info.get('description', ''),
                thumbnail_url = info.get('screenshot', ''),
            )
        )
        if not created:
            b.description = info['title']
            b.extended = info.get('description', '')
            b.thumbnail_url = info.get('screenshot', ''),
            b.save()
        return Item.objects.create_or_update(
            instance = b, 
            timestamp = utils.parsedate(info['created']), 
            tags = info.get('tags', ''),
            source = __name__,
            source_id = info['id'],
        )
