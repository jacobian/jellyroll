Prerequisites
-------------

Required by setup.py:

    * django-tagging (0.3pre)
    * Django 1.0+
    * PIL
    * python-dateutil
    * pytz

Optional
--------

* GitPython (for Git support)
* pysvn (for SVN support)
* feedparser (for YouTube support)

Installation
------------

You need to set up which providers you are going to use, e.g.

::

  JELLYROLL_PROVIDERS = (
      'jellyroll.providers.delicious',
      'jellyroll.providers.flickr',
  )