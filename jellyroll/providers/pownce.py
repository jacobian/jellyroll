import datetime
import logging
from django.conf import settings
from django.db import transaction
from jellyroll.providers import utils
from jellyroll.models import Item, Message

POWNCE_URL =  "http://api.pownce.com/2.0/note_lists/%s.json?type=%s&page=%s&limit=100"

#
# Public API
#

log = logging.getLogger("jellyroll.providers.pownce")

def enabled():
    ok = hasattr(settings, 'POWNCE_USERNAME')
    if not ok:
        log.warn('The Pownce provider is not available because the '
                 'POWNCE_USERNAME settings is undefined.')
    return ok

def update():
    page = 0
    done = False
    while not done:
        log.debug("Fetching page %s", page)
        resp = utils.getjson(POWNCE_URL % (settings.POWNCE_USERNAME, 'messages', page))
        if resp.has_key('error') and resp['error']['status_code'] == 404:
            log.debug("Ran out of results; finishing.")
            break
        
        for message in resp['notes']:
            if _item_already_exists(message['id']):
                log.debug("Found note that already exists (%s); finishing.", message['id'])
                done = True
                break
            _handle_message(
                id = message['id'], 
                timestamp = datetime.datetime.fromtimestamp(message['timestamp']),
                message = message['body']
            )
        
        page += 1

#
# Private API
#

def _item_already_exists(id):
    try:
        Item.objects.get(source=__name__, source_id=str(id))
    except Item.DoesNotExist:
        return False
    else:
        return True

@transaction.commit_on_success
def _handle_message(id, timestamp, message):
    log.debug("Handling message ID %s", id)
    m, created = Message.objects.get_or_create(message=message)
    if created:
        return Item.objects.create_or_update(
            instance = m, 
            timestamp = timestamp,
            source = __name__,
            source_id = str(id),
        )
