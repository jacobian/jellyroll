Prerequisites
-------------

* Django 1.0
* PIL
* dateutil
* django-tagging, SVN r149+


Installation
------------
You need to set up which providers you are going to use, e.g.

::

  JELLYROLL_PROVIDERS = (
      'jellyroll.providers.delicious',
      'jellyroll.providers.flickr',
  )