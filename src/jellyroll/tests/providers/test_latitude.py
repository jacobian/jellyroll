import mock
import decimal
from django.test import TestCase
from jellyroll.providers import latitude
from jellyroll.models import Item

# The Latitude "API" response
LOCATION_INFO = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [-95.260607, 38.942639]
        },
        "properties": {
            "id": "8256516920795551601",
            "accuracyInMeters": 0,
            "timeStamp": 1250601047,
            "reverseGeocode": "Lawrence, KS, USA",
            "photoUrl": "http://www.example.com/",
            "photoWidth": 96,
            "photoHeight": 96,
            "placardUrl": "http://www.example.com/",
            "placardWidth": 56,
            "placardHeight": 59
        }
    }]
}

mock_getjson = mock.Mock()
mock_getjson.return_value = LOCATION_INFO

class LatitudeProviderTests(TestCase):
    
    def test_enabled(self):
        self.assertEqual(latitude.enabled(), True)
    
    @mock.patch('jellyroll.providers.utils.getjson', mock_getjson)
    def test_update(self):
        latitude.update()
        items = Item.objects.filter(content_type__model='location').order_by('-timestamp')        
        loc = items[0].object
        self.assertEqual(loc.longitude, decimal.Decimal('-95.260607'))
        self.assertEqual(loc.latitude, decimal.Decimal('38.942639'))
        self.assertEqual(loc.name, "Lawrence, KS, USA")
        