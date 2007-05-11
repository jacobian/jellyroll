import datetime
from django.test import TestCase
from django.conf import settings
from jellyroll.models import Item

class TestYearView(TestCase):
    fixtures = ["bookmarks.json", "photos.json", "trac.json", "tracks.json", "videos.json", "websearches.json"]
    
    def setUp(self):
        settings.ROOT_URLCONF = "jellyroll.urls.calendar"
        
    def testYearView(self):
        year = datetime.date.today().year
        response = self.client.get("/%s/" % year)
        self.assertEqual(response.context[0]["year"], year)
        self.assertEqual(len(response.context[0]["items"]), Item.objects.filter(timestamp__year=year).count())