Prerequisites
-------------

* Django 1.0
* PIL
* dateutil
* django-tagging, SVN r149+

Optional
--------

* pytz (1)

Notes
-----

1. pytz is included in order to support date translation of providers whose sources
   do not syndicate item dates in your local timezone (typically these services have
   settings for which you can specify your timezone). These services currently include:

  * gitscm (stores all dates UTC as time_struct)
  * lastfm (publishes all dates in RSS as UTC timestamp)
  * twitter (publishes all dates in RSS as UTC string)