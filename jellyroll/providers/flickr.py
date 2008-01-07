import datetime
import logging
import urllib
from django.conf import settings
from django.db import transaction
from django.utils.encoding import smart_unicode
from jellyroll.models import Item, Photo
from jellyroll.providers import utils

log = logging.getLogger("jellyroll.providers.flickr")

#
# Mini FlickrClient API
#

class FlickrError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
    def __str__(self):
        return 'FlickrError %s: %s' % (self.code, self.message)

class FlickrClient(object):
    def __init__(self, api_key, method='flickr'):
        self.api_key = api_key
        self.method = method
        
    def __getattr__(self, method):
        return FlickrClient(self.api_key, '%s.%s' % (self.method, method))
        
    def __repr__(self):
        return "<FlickrClient: %s>" % self.method
        
    def __call__(self, **params):
        params['method'] = self.method
        params['api_key'] = self.api_key
        params['format'] = 'json'
        params['nojsoncallback'] = '1'
        url = "http://flickr.com/services/rest/?" + urllib.urlencode(params)
        json = utils.getjson(url)
        if json.get("stat", "") == "fail":
            raise FlickrError(json["code"], json["message"])
        return json

#
# Public API
#
def enabled():
    return (hasattr(settings, "FLICKR_API_KEY") and
            hasattr(settings, "FLICKR_USER_ID") and
            hasattr(settings, "FLICKR_USERNAME"))

def update():
    flickr = FlickrClient(settings.FLICKR_API_KEY)
    
    # Preload the list of licenses
    licenses = licenses = flickr.photos.licenses.getInfo()
    licenses = dict((l["id"], smart_unicode(l["url"])) for l in licenses["licenses"]["license"])
    
    # Handle update by pages until we see photos we've already handled
    last_update_date = Item.objects.get_last_update_of_model(Photo)
    page = 1
    while True:
        log.debug("Fetching page %s of photos", page)
        resp = flickr.people.getPublicPhotos(user_id=settings.FLICKR_USER_ID, extras="license,date_taken", per_page="50", page=str(page))
        photos = resp["photos"]
        if page > photos["pages"]:
            log.debug("Ran out of photos; stopping.")
            break
            
        for photodict in photos["photo"]:
            timestamp = utils.parsedate(str(photodict["datetaken"]))
            if timestamp < last_update_date:
                log.debug("Hit an old photo (taken %s; last update was %s); stopping.", timestamp, last_update_date)
                break
            
            photo_id = utils.safeint(photodict["id"])
            license = licenses[photodict["license"]]
            secret = smart_unicode(photodict["secret"])
            server = smart_unicode(photodict["server"])
            _handle_photo(flickr, photo_id, secret, license, timestamp)
            
        page += 1
        
#
# Private API
#

@transaction.commit_on_success
def _handle_photo(flickr, photo_id, secret, license, timestamp):
    info = flickr.photos.getInfo(photo_id=photo_id, secret=secret)["photo"]
    server_id = utils.safeint(info["server"])
    taken_by = smart_unicode(info["owner"]["username"])
    title = smart_unicode(info["title"]["_content"])
    description = smart_unicode(info["description"]["_content"])
    comment_count = utils.safeint(info["comments"]["_content"])
    date_uploaded = datetime.datetime.fromtimestamp(utils.safeint(info["dates"]["posted"]))
    date_updated = datetime.datetime.fromtimestamp(utils.safeint(info["dates"]["lastupdate"]))
    
    log.debug("Handling photo: %r (taken %s)" % (title, timestamp))
    photo, created = Photo.objects.get_or_create(
        photo_id      = photo_id,
        defaults = dict(
            server_id     = server_id,
            secret        = secret,
            taken_by      = taken_by,
            cc_license    = license,
            title         = title,
            description   = description,
            comment_count = comment_count,
            date_uploaded = date_uploaded,
            date_updated  = date_updated,
        )
    )
    if created:
        photo.exif = _convert_exif(flickr.photos.getExif(photo_id=photo_id, secret=secret))
    else:
        photo.server_id     = server_id
        photo.secret        = secret
        photo.taken_by      = taken_by
        photo.cc_license    = license
        photo.title         = title
        photo.description   = description
        photo.comment_count = comment_count
        photo.date_uploaded = date_uploaded
        photo.date_updated  = date_updated
    photo.save()
    
    return Item.objects.create_or_update(
        instance = photo, 
        timestamp = timestamp,
        tags = _convert_tags(info["tags"]),
        source = __name__,
    )

def _convert_exif(exif):
    converted = {}
    for e in exif["photo"]["exif"]:
        key = smart_unicode(e["label"])
        val = e.get("clean", e["raw"])["_content"]
        val = smart_unicode(val)
        converted[key] = val
    return converted

def _convert_tags(tags):
    return " ".join(set(t["_content"] for t in tags["tag"] if not t["machine_tag"]))