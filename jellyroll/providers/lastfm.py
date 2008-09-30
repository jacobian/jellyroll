import datetime
import urllib
import logging
from django.conf import settings
from django.db import transaction
from django.utils.encoding import smart_unicode
from httplib2 import HttpLib2Error
from jellyroll.providers import utils
from jellyroll.models import Item, Track
from django.template.defaultfilters import slugify

try:
    set
except NameError:
    from sets import Set as set     # Python 2.3 fallback

#
# API URLs
#

RECENT_TRACKS_URL = "http://ws.audioscrobbler.com/1.0/user/%s/recenttracks.xml"
TRACK_TAGS_URL    = "http://ws.audioscrobbler.com/1.0/track/%s/%s/toptags.xml"
ARTIST_TAGS_URL   = "http://ws.audioscrobbler.com/1.0/artist/%s/toptags.xml"

#
# Public API
#

log = logging.getLogger("jellyroll.providers.lastfm")

def enabled():
    return hasattr(settings, 'LASTFM_USERNAME')

def update():
    last_update_date = Item.objects.get_last_update_of_model(Track)
    log.debug("Last update date: %s", last_update_date)
    
    xml = utils.getxml(RECENT_TRACKS_URL % settings.LASTFM_USERNAME)
    for track in xml.getiterator("track"):
        artist      = track.find('artist')
        artist_name = smart_unicode(artist.text)
        artist_mbid = artist.get('mbid')
        track_name  = smart_unicode(track.find('name').text)
        track_mbid  = smart_unicode(track.find('mbid').text)
        url         = smart_unicode(track.find('url').text)
        timestamp   = datetime.datetime.fromtimestamp(int(track.find('date').get('uts')))
        if timestamp > last_update_date:
            log.debug("Handling track: %r - %r", artist_name, track_name)
            tags = _tags_for_track(artist_name, track_name)
            _handle_track(artist_name, artist_mbid, track_name, track_mbid, url, timestamp, tags)

#
# Private API
#

def _tags_for_track(artist_name, track_name):
    """
    Get the top tags for a track. Also fetches tags for the artist. Only
    includes tracks that break a certain threshold of usage, defined by
    settings.LASTFM_TAG_USAGE_THRESHOLD (which defaults to 15).
    """
    
    urls = [
        ARTIST_TAGS_URL % (urllib.quote(artist_name)),
        TRACK_TAGS_URL % (urllib.quote(artist_name), urllib.quote(track_name)),
    ]
    tags = set()
    for url in urls:
        log.debug("Fetching tags from %r", url)
        try:
            xml = utils.getxml(url)
        except HttpLib2Error, e:
            if e.code == 408:
                return ""
            else:
                raise
        for t in xml.getiterator("tag"):
            count = utils.safeint(t.find("count").text)
            if count >= getattr(settings, 'LASTFM_TAG_USAGE_THRESHOLD', 15):
                tags.add(slugify(smart_unicode(t.find("name").text)))            
    return " ".join(tags)

def _handle_track(artist_name, artist_mbid, track_name, track_mbid, url, timestamp, tags):
    t = Track(
        artist_name = artist_name,
        track_name  = track_name,
        url         = url,
        track_mbid  = track_mbid is not None and track_mbid or '',
        artist_mbid = artist_mbid is not None and artist_mbid or '',
    )
    return Item.objects.create_or_update(
        instance = t, 
        timestamp = timestamp, 
        tags = tags,
        source = __name__
    )
_handle_track = transaction.commit_on_success(_handle_track)
