import datetime
import feedparser
import urlparse
import logging
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import tzinfo
from django.utils.encoding import smart_unicode
from jellyroll.models import Item, SearchEngine, WebSearch, WebSearchResult
from jellyroll.models import VideoSource, Video
from jellyroll.providers import utils

RSS_URL = "https://%s:%s@www.google.com/searchhistory/?output=rss"
VIDEO_TAG_URL = "http://video.google.com/tags?docid=%s"

# Monkeypatch feedparser to understand smh:query_guid elements
feedparser._FeedParserMixin._start_smh_query_guid = lambda self, attrs: self.push("query_guid", 1)

log = logging.getLogger("jellyroll.providers.gsearch")

#
# Public API
#

def enabled():
    return hasattr(settings, 'GOOGLE_USERNAME') and hasattr(settings, 'GOOGLE_PASSWORD')
    
def update():
    feed = feedparser.parse(RSS_URL % (settings.GOOGLE_USERNAME, settings.GOOGLE_PASSWORD))
    for entry in feed.entries:
        if entry.tags[0].term == "web query":
            _handle_query(entry)
        elif entry.tags[0].term == "web result":
            _handle_result(entry)
        elif entry.tags[0].term == "video result":
            _handle_video(entry)
        
#
# Private API
#

# Shortcut
CT = ContentType.objects.get_for_model

@transaction.commit_on_success
def _handle_query(entry):
    engine = SearchEngine.objects.get(name="Google")
    guid = smart_unicode(urlparse.urlsplit(entry.guid)[2].replace("/searchhistory/", ""))
    query = smart_unicode(entry.title)
    timestamp = datetime.datetime(tzinfo=tzinfo.FixedOffset(0), *entry.updated_parsed[:6])
    
    log.debug("Handling Google query for %r", query)
    try:
        item = Item.objects.get(
            content_type = CT(WebSearch),
            source = __name__,
            source_id = guid
        )
    except Item.DoesNotExist:
        item = Item.objects.create_or_update(
            instance = WebSearch(engine=engine, query=query), 
            timestamp = timestamp,
            source = __name__,
            source_id = guid,
        )
    
@transaction.commit_on_success
def _handle_result(entry):
    guid = smart_unicode(entry.query_guid)
    title = smart_unicode(entry.title)
    url = smart_unicode(entry.link)

    log.debug("Adding search result: %r" % url)
    try:
        item = Item.objects.get(
            content_type = CT(WebSearch),
            source = __name__,
            source_id = guid
        )
    except Item.DoesNotExist:
        log.debug("Skipping unknown query GUID: %r" % guid)
        return
    
    WebSearchResult.objects.get_or_create(
        search = item.object,
        url = url,
        defaults = {'title' : title},
    )
    
@transaction.commit_on_success
def _handle_video(entry):
    vs = VideoSource.objects.get(name="Google")
    url = smart_unicode(entry.link)
    title = smart_unicode(entry.title)
    timestamp = datetime.datetime(tzinfo=tzinfo.FixedOffset(0), *entry.updated_parsed[:6])
    
    log.debug("Adding viewed video: %r" % title)
    vid, created = Video.objects.get_or_create(
        source = vs,
        url = url,
        defaults = {'title' : title},
    )
    return Item.objects.create_or_update(
        instance = vid, 
        timestamp = timestamp,
        source = __name__,
    )