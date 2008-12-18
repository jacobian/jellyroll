import md5
import datetime
import logging
from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import slugify
from django.utils.functional import memoize
from django.utils.http import urlquote
from django.utils.encoding import smart_str, smart_unicode
from httplib2 import HttpLib2Error
from jellyroll.providers import utils
from jellyroll.models import Item, Message

#
# API URLs
#

RECENT_STATUSES_URL = "http://twitter.com/statuses/user_timeline/%s.rss"

#
# Public API
#

log = logging.getLogger("jellyroll.providers.twitter")

def enabled():
    return True

def update():
    last_update_date = Item.objects.get_last_update_of_model(Message)
    log.debug("Last update date: %s", last_update_date)
    
    xml = utils.getxml(RECENT_STATUSES_URL % settings.TWITTER_USERNAME)
    for status in xml.getiterator("item"):
        message      = status.find('title')
        message_text = smart_unicode(message.text)
        url          = smart_unicode(status.find('link').text)
        # perhaps i'm a rube, but it doesn't seem strptime will take a %z formatting argument :/
        timestamp    = datetime.datetime.strptime(status.find('pubDate').text[:-6],"%a, %d %b %Y %H:%M:%S")
        if not _status_exists(message_text, url, timestamp):
            _handle_status(message_text, url, timestamp)

#
# Private API
#

@transaction.commit_on_success
def _handle_status(message_text, url, timestamp):
    t = Message(
        message = message_text,
        )
    if not _status_exists(message_text, url, timestamp):
        log.debug("Saving message: %r", message_text)
        item = Item.objects.create_or_update(
            instance = t,
            timestamp = timestamp,
            source = __name__,
            source_id = _source_id(message_text, url, timestamp),
            url = url,
            )
        item.save()
        
def _source_id(message_text, url, timestamp):
    return md5.new(smart_str(message_text) + smart_str(url) + str(timestamp)).hexdigest()
    
def _status_exists(message_text, url, timestamp):
    id = _source_id(message_text, url, timestamp)
    try:
        Item.objects.get(source=__name__, source_id=id)
    except Item.DoesNotExist:
        return False
    else:
        return True

