import datetime
from django.test import TestCase
from django.conf import settings
from jellyroll.models import Item

class CalendarViewTest(TestCase):
    fixtures = ["bookmarks.json", "photos.json", "trac.json", "tracks.json", "videos.json", "websearches.json"]
    
    def setUp(self):
        settings.ROOT_URLCONF = "jellyroll.urls.calendar"
        
    def callView(self, url):
        today = datetime.date.today()
        response = self.client.get(today.strftime(url).lower())
        if isinstance(response.context, list):
            context = response.context[0]
        else:
            context = response.context
        return today, response, context
        
    def testYearView(self):
        today, response, context = self.callView("/%Y/")
        self.assertEqual(context["year"], today.year)
        self.assertEqual(len(context["items"]), Item.objects.count())
        
    def testMonthView(self):
        today, response, context = self.callView("/%Y/%b/")
        self.assertEqual(context["month"].year, today.year)
        self.assertEqual(context["month"].month, today.month)
        self.assertEqual(len(context["items"]), Item.objects.count())
        
    def testDayView(self):
        today, response, context = self.callView("/%Y/%b/%d/")
        self.assertEqual(context["day"], today)
        self.assertEqual(len(context["items"]), Item.objects.count())
        
    def testTodayView(self):
        today, response, context = self.callView("/")
        self.assertEqual(context["day"], today)
        self.assertEqual(len(context["items"]), Item.objects.count())
        self.assertEqual(context["is_today"], True)
        self.assertTemplateUsed(response, "jellyroll/calendar/today.html")
        
    def testDayViewOrdering(self):
        today, response, context = self.callView("/%Y/%b/%d/")
        first = context["items"][0].timestamp
        last = list(context["items"])[-1].timestamp
        self.assert_(first < last, "first: %s, last: %s" % (first, last))
        
    def testTodayViewOrdering(self):
        today, response, context = self.callView("/")
        first = context["items"][0].timestamp
        last = list(context["items"])[-1].timestamp
        self.assert_(first > last, "first: %s, last: %s" % (first, last))