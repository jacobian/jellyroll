import datetime
import logging
import xmlrpclib
from django.conf import settings
from django.db import transaction
from django.utils.encoding import smart_unicode
from jellyroll.models import Item, VideoSource, Video
from jellyroll.providers import utils

# Isn't xmlrpclib nifty?
youtube = xmlrpclib.Server("http://www.youtube.com/api2_xmlrpc").youtube

log = logging.getLogger("jellyroll.providers.youtube")

#
# Public API
#
def enabled():
    return hasattr(settings, "YOUTUBE_USERNAME") and hasattr(settings, "YOUTUBE_DEVELOPER_ID")

def update():
    res = youtube.users.list_favorite_videos({
        "dev_id" : settings.YOUTUBE_DEVELOPER_ID,
        "user" : settings.YOUTUBE_USERNAME
    })
    xml = utils.ET.fromstring(res)
    for video in xml.getiterator("video"):
        title = smart_unicode(video.find("title").text)
        url = smart_unicode(video.find("url").text)
        tags = smart_unicode(video.find("tags").text).lower()
        # suckage: youtube doesn't expose the date a movie was favorited :(
        timestamp = datetime.datetime.now()
        log.debug("Handling video: %r" % title)
        _handle_video(title, url, tags, timestamp)
        
#
# Private API
#

def _handle_video(title, url, tags, timestamp):
    source = VideoSource.objects.get(name="YouTube")
    vid, created = Video.objects.get_or_create(url=url, defaults={'title': title, 'source': source})
    return Item.objects.create_or_update(
        instance = vid, 
        timestamp = timestamp,
        tags = tags,
        source = __name__,
    )
_handle_video = transaction.commit_on_success(_handle_video)