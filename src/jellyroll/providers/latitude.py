"""
Provide location from Google Latitude.

Requires that you've turned on public location at
http://www.google.com/latitude/apps/badge.
"""

import logging
from django.conf import settings
from django.db import transaction
from jellyroll.models import Location
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
    _update_location(settings.GOOGLE_LATITUDE_USER_ID)
        
#
# Private API
#

@transaction.commit_on_success
def _update_location(user_id):
    json = utils.getjson('http://www.google.com/latitude/apps/badge/api?user=%s&type=json' % user_id)
    lng, lat = map(str, json['features'][0]['geometry']['coordinates'])
    name = json['features'][0]['properties']['reverseGeocode']
    Location.objects.create(latitude=lat, longitude=lng, name=name)