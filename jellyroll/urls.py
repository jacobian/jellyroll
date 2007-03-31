import jellyroll.views import calendar
from django.conf.urls.defaults import *

urlpatterns = patterns(
    ('^$',                           calendar.today),
    ('^(\d{4})/$',                   calendar.year),
    ('^(\d{4})/(\w{3})/$',           calendar.month),
    ('^(\d{4})/(\w{3})/(\d{1,2})/$', calendar.day),
)