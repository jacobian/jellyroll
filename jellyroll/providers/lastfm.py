import datetime
import urllib
import logging
from django.conf import settings
from django.db import transaction
from jellyroll.providers import utils
from jellyroll.models import Item, Track
from django.template.defaultfilters import slugify

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
        artist_name = utils.safestr(artist.text)
        artist_mbid = artist.get('mbid')
        track_name  = utils.safestr(track.find('name').text)
        track_mbid  = utils.safestr(track.find('mbid').text)
        url         = utils.safestr(track.find('url').text)
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
        xml = utils.getxml(url)
        for t in xml.getiterator("tag"):
            count = utils.safeint(t.find("count").text)
            if count >= getattr(settings, 'LASTFM_TAG_USAGE_THRESHOLD', 15):
                tags.add(slugify(utils.safestr(t.find("name").text)))            
    return " ".join(tags)

@transaction.commit_on_success      
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

