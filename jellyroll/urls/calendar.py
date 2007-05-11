"""
URLs for doing a jellyroll site by date (i.e. ``2007/``, ``2007/may/``, etc.)
"""

from django.conf.urls.defaults import *

urlpatterns = patterns('jellyroll.views.calendar', 
    url(
        regex = "^$",
        view  = "recent",
        name  = "jellyroll_calendar_recent",
    ),
    url(
        regex = "^(?P<year>\d{4})/$",
        view  = "year",
        name  = "jellyroll_calendar_year",
    ),
    url(
        regex = "^(?P<year>\d{4})/(?P<month>\w{3})/$",
        view  = "month",
        name  = "jellyroll_calendar_month",
    ),
    url(
        regex = "^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{2})/$",
        view  = "day",
        name  = "jellyroll_calendar_day",
    ),
)