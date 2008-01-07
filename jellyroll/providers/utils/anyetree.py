"""
Get an Etree library.  Usage::

    >>> from anyetree import etree

Returns some etree library. Looks for (in order of decreasing preference):

    * ``lxml.etree`` (http://cheeseshop.python.org/pypi/lxml/)
    * ``xml.etree.cElementTree`` (built into Python 2.5)
    * ``cElementTree`` (http://effbot.org/zone/celementtree.htm)
    * ``xml.etree.ElementTree`` (built into Python 2.5)
    * ``elementree.ElementTree (http://effbot.org/zone/element-index.htm)
"""

__all__ = ['etree']

SEARCH_PATHS = [
    "lxml.etree",
    "xml.etree.cElementTree",
    "cElementTree",
    "xml.etree.ElementTree",
    "elementtree.ElementTree",
]

etree = None

for name in SEARCH_PATHS:
    try:
        etree = __import__(name, '', '', [''])
        break
    except ImportError:
        continue

if etree is None:
    raise ImportError("No suitable ElementTree implementation found.")