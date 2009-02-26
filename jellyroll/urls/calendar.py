"""
URLs for doing a jellyroll site by date (i.e. ``2007/``, ``2007/may/``, etc.)
"""

from django.conf.urls.defaults import *
from jellyroll.views import calendar

urlpatterns = patterns('', 
    url(
        regex = "^$",
        view  = calendar.today,
        name  = "jellyroll_calendar_today",
    ),
    url(
        regex = "^(?P<year>\d{4})/$",
        view  = calendar.year,
        name  = "jellyroll_calendar_year",
    ),
    url(
        regex = "^(?P<year>\d{4})/(?P<month>\w{3})/$",
        view  = calendar.month,
        name  = "jellyroll_calendar_month",
    ),
    url(
        regex = "^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{2})/$",
        view  = calendar.day,
        name  = "jellyroll_calendar_day",
    ),
)
