"""
Provide location from Google Latitude.

Requires that you've turned on public location at
http://www.google.com/latitude/apps/badge.
"""

import datetime
import logging
from django.conf import settings
from django.db import transaction
from jellyroll.models import Location, Item
from jellyroll.providers import utils

log = logging.getLogger("jellyroll.providers.latitude")

#
# Public API
#
def enabled():
    ok = hasattr(settings, 'GOOGLE_LATITUDE_USER_ID')
    if not ok:
        log.warn('The Latitude provider is not available because the '
                 'GOOGLE_LATITUDE_USER_ID settings is undefined.')
    return ok

def update():
    last_update_date = Item.objects.get_last_update_of_model(Location)
    log.debug("Last update date: %s", last_update_date)
    _update_location(settings.GOOGLE_LATITUDE_USER_ID, since=last_update_date)
        
#
# Private API
#

@transaction.commit_on_success
def _update_location(user_id, since):
    json = utils.getjson('http://www.google.com/latitude/apps/badge/api?user=%s&type=json' % user_id)
    feature = json['features'][0]
    
    lat, lng = map(str, feature['geometry']['coordinates'])
    name = feature['properties']['reverseGeocode']
    timestamp = datetime.datetime.fromtimestamp(feature['properties']['timeStamp'])
    if timestamp > since:
        log.debug("New location: %s", name)
        loc = Location(latitude=lat, longitude=lng, name=name)
        return Item.objects.create_or_update(
            instance = loc,
            timestamp = timestamp,
            source = __name__,
            source_id = str(feature['properties']['timeStamp']),
        )