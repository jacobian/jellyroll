import urllib
import urlparse
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.utils import simplejson, text
from django.utils.encoding import smart_unicode
from jellyroll.managers import ItemManager
from tagging.fields import TagField

class Item(models.Model):
    """
    A generic jellyroll item. Slightly denormalized for performance.
    """
    
    # Generic relation to the object.
    content_type = models.ForeignKey(ContentType)
    object_id = models.TextField()
    object = generic.GenericForeignKey('content_type', 'object_id')
    
    # "Standard" metadata each object provides.
    url = models.URLField(blank=True)
    timestamp = models.DateTimeField()
    tags = TagField(max_length=2500)
    
    # Metadata about where the object "came from" -- used by data providers to
    # figure out which objects to update when asked.
    source = models.CharField(max_length=100, blank=True)
    source_id = models.TextField(blank=True)
    
    # Denormalized object __unicode__, for performance 
    object_str = models.TextField(blank=True)
    
    objects = ItemManager()
    
    class Meta:
        ordering = ['-timestamp']
        unique_together = [("content_type", "object_id")]
    
    def __unicode__(self):
        return "%s: %s" % (self.content_type.model_class().__name__, self.object_str)
        
    def __cmp__(self, other):
        return cmp(self.timestamp, other.timestamp)
    
    def save(self, force_insert=False, force_update=False):
        ct = "%s_%s" % (self.content_type.app_label, self.content_type.model.lower())
        self.object_str = smart_unicode(self.object)
        if hasattr(self.object, "url"):
            self.url = self.object.url
        super(Item, self).save(force_insert, force_update)

class Bookmark(models.Model):
    """
    A bookmarked link. The model is based on del.icio.us, with the added
    thumbnail field for ma.gnolia users.
    """
    
    url           = models.URLField(unique=True)
    description   = models.CharField(max_length=255)
    extended      = models.TextField(blank=True)
    thumbnail     = models.ImageField(upload_to="img/jellyroll/bookmarks/%Y/%m", blank=True)
    thumbnail_url = models.URLField(blank=True, verify_exists=False)
    
    def __unicode__(self):
        return self.url

class Track(models.Model):
    """A track you listened to. The model is based on last.fm."""
    
    artist_name = models.CharField(max_length=250)
    track_name  = models.CharField(max_length=250)
    url         = models.URLField(blank=True)
    track_mbid  = models.CharField("MusicBrainz Track ID", max_length=36, blank=True)
    artist_mbid = models.CharField("MusicBrainz Artist ID", max_length=36, blank=True)
    
    def __unicode__(self):
        return "%s - %s" % (self.artist_name, self.track_name)

CC_LICENSES = (
    ('http://creativecommons.org/licenses/by/2.0/',         'CC Attribution'),
    ('http://creativecommons.org/licenses/by-nd/2.0/',      'CC Attribution-NoDerivs'),
    ('http://creativecommons.org/licenses/by-nc-nd/2.0/',   'CC Attribution-NonCommercial-NoDerivs'),
    ('http://creativecommons.org/licenses/by-nc/2.0/',      'CC Attribution-NonCommercial'),
    ('http://creativecommons.org/licenses/by-nc-sa/2.0/',   'CC Attribution-NonCommercial-ShareAlike'),
    ('http://creativecommons.org/licenses/by-sa/2.0/',      'CC Attribution-ShareAlike'),
)

class Photo(models.Model):
    """
    A photo someone took. This person could be you, in which case you can
    obviously do whatever you want with it. However, it could also have been
    taken by someone else, so in that case there's a few fields for storing the
    object's rights.
    
    The model is based on Flickr, and won't work with anything else :(
    """
    
    # Key Flickr info
    photo_id    = models.CharField(unique=True, primary_key=True, max_length=50)
    server_id   = models.PositiveSmallIntegerField()
    secret      = models.CharField(max_length=30, blank=True)
    
    # Rights metadata
    taken_by    = models.CharField(max_length=100, blank=True)
    cc_license  = models.URLField(blank=True, choices=CC_LICENSES)
    
    # Main metadata
    title           = models.CharField(max_length=250)
    description     = models.TextField(blank=True)
    comment_count   = models.PositiveIntegerField(max_length=5, default=0)
    
    # Date metadata
    date_uploaded = models.DateTimeField(blank=True, null=True)
    date_updated  = models.DateTimeField(blank=True, null=True)
    
    # EXIF metadata
    _exif = models.TextField(blank=True)
    def _set_exif(self, d):
        self._exif = simplejson.dumps(d)
    def _get_exif(self):
        if self._exif:
            return simplejson.loads(self._exif)
        else:
            return {}
    exif = property(_get_exif, _set_exif, "Photo EXIF data, as a dict.")
    
    def __unicode__(self):
        return self.title
    
    def url(self):
        return "http://www.flickr.com/photos/%s/%s/" % (self.taken_by, self.photo_id)
    url = property(url)
        
    def timestamp(self):
        return self.date_uploaded
    timestamp = property(timestamp)
    
    ### Image URLs ###
    
    def get_image_url(self, size=None):
        if size in list('mstbo'):
            return "http://static.flickr.com/%s/%s_%s_%s.jpg" % (self.server_id, self.photo_id, self.secret, size)
        else:
            return "http://static.flickr.com/%s/%s_%s.jpg" % (self.server_id, self.photo_id, self.secret)
    
    image_url       = property(lambda self: self.get_image_url())
    square_url      = property(lambda self: self.get_image_url('s'))
    thumbnail_url   = property(lambda self: self.get_image_url('t'))
    small_url       = property(lambda self: self.get_image_url('m'))
    large_url       = property(lambda self: self.get_image_url('b'))
    original_url    = property(lambda self: self.get_image_url('o'))
    
    ### Rights ###
    
    def license_code(self):
        if not self.cc_license:
            return None
        path = urlparse.urlparse(self.cc_license)[2]
        return path.split("/")[2]
    license_code = property(license_code)
    
    def taken_by_me(self):
        return self.taken_by == getattr(settings, "FLICKR_USERNAME", "")
    taken_by_me = property(taken_by_me)
    
    def can_republish(self):
        """
        Is it OK to republish this photo, or must it be linked only?
        """
        
        # If I took the photo, then it's always OK to republish.
        if self.taken_by_me:
            return True
        
        # If the photo has no CC license, then it's never OK to republish.
        elif self.license_code is None:
            return False
        
        # If the settings flags this site as "commercial" and it's an NC
        # license, then no republish for you.
        elif getattr(settings, "SITE_IS_COMMERCIAL", False) and "nc" in self.license_code:
            return False
        
        # Otherwise, we're OK to republish it.
        else:
            return True
    can_republish = property(can_republish)
    
    def derivative_ok(self):
        """Is it OK to produce derivative works?"""
        return self.can_republish and "nd" not in self.license_code
    derivative_ok = property(derivative_ok)
    
    def must_share_alike(self):
        """Must I share derivative works?"""
        return self.can_republish and "sa" in self.license_code
    must_share_alike = property(must_share_alike)

class SearchEngine(models.Model):
    """
    Simple encapsulation of a search engine.
    """
    name = models.CharField(max_length=200)
    home = models.URLField()
    search_template = models.URLField()
    
    def __unicode__(self):
        return self.name
        
class WebSearch(models.Model):
    """
    A search made with a search engine. Modeled after Google's search history,
    but (may/could/will) work with other sources.
    """
    engine = models.ForeignKey(SearchEngine, related_name="searches")
    query = models.CharField(max_length=250)
    
    class Meta:
        verbose_name_plural = "web searches"

    def __unicode__(self):
        return self.query
        
    def url(self):
        return self.engine.search_template % (urllib.quote_plus(self.query))
    url = property(url)
        
class WebSearchResult(models.Model):
    """
    A page viewed as a result of a WebSearch
    """
    search = models.ForeignKey(WebSearch, related_name="results")
    title  = models.CharField(max_length=250)
    url    = models.URLField()

    def __unicode__(self):
        return self.title

class VideoSource(models.Model):
    """
    A place you might view videos. Basically just an encapsulation for the
    "embed template" bit.
    """
    name = models.CharField(max_length=200)
    home = models.URLField()
    embed_template = models.URLField()
    
    def __unicode__(self):
        return self.name

class Video(models.Model):
    """A video you viewed."""
    
    source = models.ForeignKey(VideoSource, related_name="videos")
    title  = models.CharField(max_length=250)
    url    = models.URLField()

    def __unicode__(self):
        return self.title
        
    def docid(self):
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(self.url)
        return query.split("=")[-1]
    docid = property(docid)
        
    def embed_url(self):
        return self.source.embed_template % self.docid
    embed_url = property(embed_url)

SCM_CHOICES = (
    ("svn", "Subversion"),
    ("git", "Git"),
)

class CodeRepository(models.Model):
    """
    A code repository that you check code into somewhere. Currently only SVN
    is supported, but other forms should be hard to support.
    """
    type = models.CharField(max_length=10, choices=SCM_CHOICES)
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    username = models.CharField(max_length=100, help_text="Your username/email for this SCM.")
    public_changeset_template = models.URLField(
        verify_exists = False, blank = True,
        help_text = "Template for viewing a changeset publically. Use '%s' for the revision number")
    url = models.URLField()

    class Meta:
        verbose_name_plural = "code repositories"

    def __unicode__(self):
        return self.name

class CodeCommit(models.Model):
    """
    A code change you checked in.
    """
    repository = models.ForeignKey(CodeRepository, related_name="commits")
    revision = models.CharField(max_length=200)
    message = models.TextField()

    class Meta:
        ordering = ["-revision"]

    def __unicode__(self):
        return "[%s] %s" % (self.format_revision(), text.truncate_words(self.message, 10))

    def format_revision(self):
        """
        Shorten hashed revisions for nice reading.
        """
        try:
            return str(int(self.revision))
        except ValueError:
            return self.revision[:7]

    def url(self):
        if self.repository.public_changeset_template:
            return self.repository.public_changeset_template % self.revision
        return ""
    url = property(url)

# Register item objects to be "followed"
Item.objects.follow_model(Bookmark)
Item.objects.follow_model(Track)
Item.objects.follow_model(Photo)
Item.objects.follow_model(WebSearch)
Item.objects.follow_model(Video)
Item.objects.follow_model(CodeCommit)
