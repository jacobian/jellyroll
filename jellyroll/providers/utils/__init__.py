import httplib2
import dateutil.parser
import dateutil.tz
from django.utils import simplejson
from anyetree import etree

DEFAULT_HTTP_HEADERS = {
    "User-Agent" : "Jellyroll/1.0 (http://code.google.com/p/jellyroll)"
}

#
# URL fetching sugar
#
    
def getxml(url, **kwargs):
    """Fetch and parse some XML. Returns an ElementTree"""
    xml = fetch_resource(url, **kwargs)
    return etree.fromstring(xml)
    
def getjson(url, **kwargs):
    """Fetch and parse some JSON. Returns the deserialized JSON."""
    json = fetch_resource(url, **kwargs)
    return simplejson.loads(json)

def fetch_resource(url, method="GET", body=None, username=None, password=None, headers=None):
    h = httplib2.Http(timeout=15)
    h.force_exception_to_status_code = True
    
    if username is not None or password is not None:
        h.add_credentials(username, password)
    
    if headers is None:
        headers = DEFAULT_HTTP_HEADERS.copy()
    
    response, content = h.request(url, method, body, headers)
    return content
    
#
# Date handling utils
#

def parsedate(s):
    """
    Convert a string into a (local, naive) datetime object.
    """
    dt = dateutil.parser.parse(s)
    if dt.tzinfo:
        dt = dt.astimezone(dateutil.tz.tzlocal()).replace(tzinfo=None)
    return dt

#
# String/unicode conversion utils.
#
    
def safestr(s):
    """
    Safely corerce *anything* to a string. If the object can't be str'd, an
    empty string will be returned.
    
    You can (and I do) use this for really crappy unicode handling, but it's
    a bit like killing a mosquito with a bazooka.
    """
    if s is None:
        return ""
    if isinstance(s, unicode):
        return s.encode('ascii', 'xmlcharrefreplace')
    else:
        try:
            return str(s)
        except:
            return ""
            
def safeint(s):
    """Like safestr(), but always returns an int. Returns 0 on failure."""
    try:
        return int(safestr(s))
    except ValueError:
        return 0
