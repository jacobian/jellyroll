import datetime
import hashlib
import logging
from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import slugify
from django.utils.functional import memoize
from django.utils.http import urlquote
from django.utils.encoding import smart_str, smart_unicode
from httplib2 import HttpLib2Error
from jellyroll.models import Item, Track
from jellyroll.providers import utils

#
# API URLs
#

RECENT_TRACKS_URL = "http://ws.audioscrobbler.com/1.0/user/%s/recenttracks.xml?limit=100"
TRACK_TAGS_URL    = "http://ws.audioscrobbler.com/1.0/track/%s/%s/toptags.xml"
ARTIST_TAGS_URL   = "http://ws.audioscrobbler.com/1.0/artist/%s/toptags.xml"

#
# Public API
#

log = logging.getLogger("jellyroll.providers.lastfm")

def enabled():
    ok = hasattr(settings, 'LASTFM_USERNAME')
    if not ok:
        log.warn('The Last.fm provider is not available because the '
                 'LASTFM_USERNAME settings is undefined.')
    return ok

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

        # date delivered as UTC
        timestamp = datetime.datetime.fromtimestamp(int(track.find('date').get('uts')))
        if utils.JELLYROLL_ADJUST_DATETIME:
            timestamp = utils.utc_to_local_timestamp(int(track.find('date').get('uts')))

        if not _track_exists(artist_name, track_name, timestamp):
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
        ARTIST_TAGS_URL % (urlquote(artist_name)),
        TRACK_TAGS_URL % (urlquote(artist_name), urlquote(track_name)),
    ]
    tags = set()
    for url in urls:
        tags.update(_tags_for_url(url))
        
def _tags_for_url(url):
    tags = set()
    try:
        xml = utils.getxml(url)
    except HttpLib2Error, e:
        if e.code == 408:
            return ""
        else:
            raise
    except SyntaxError:
        return ""
    for t in xml.getiterator("tag"):
        count = utils.safeint(t.find("count").text)
        if count >= getattr(settings, 'LASTFM_TAG_USAGE_THRESHOLD', 15):
            tag = slugify(smart_unicode(t.find("name").text))
            tags.add(tag[:50])
    
    return tags
            
# Memoize tags to avoid unnecessary API calls.
_tag_cache = {}
_tags_for_url = memoize(_tags_for_url, _tag_cache, 1)

@transaction.commit_on_success
def _handle_track(artist_name, artist_mbid, track_name, track_mbid, url, timestamp, tags):
    t = Track(
        artist_name = artist_name,
        track_name  = track_name,
        url         = url,
        track_mbid  = track_mbid is not None and track_mbid or '',
        artist_mbid = artist_mbid is not None and artist_mbid or '',
    )
    if not _track_exists(artist_name, track_name, timestamp):
        log.debug("Saving track: %r - %r", artist_name, track_name)
        return Item.objects.create_or_update(
            instance = t,
            timestamp = timestamp,
            tags = tags,
            source = __name__,
            source_id = _source_id(artist_name, track_name, timestamp),
        )
        
def _source_id(artist_name, track_name, timestamp):
    return hashlib.md5(smart_str(artist_name) + smart_str(track_name) + str(timestamp)).hexdigest()
    
def _track_exists(artist_name, track_name, timestamp):
    id = _source_id(artist_name, track_name, timestamp)
    try:
        Item.objects.get(source=__name__, source_id=id)
    except Item.DoesNotExist:
        return False
    else:
        return True

