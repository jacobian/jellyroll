from django.test import TestCase
from jellyroll.models import *
from tagging.models import Tag
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django import template

# shortcut
CT = ContentType.objects.get_for_model

class BookmarkTest(TestCase):
    fixtures = ["bookmarks.json"]
        
    def testItemWorkage(self):
        i = Item.objects.get(content_type=CT(Bookmark), object_id=1)
        self.assertEqual(i.url, i.object.url)
        self.assertEqual(i.object_str, str(i.object))
            
class TrackTest(TestCase):
    fixtures = ["tracks.json"]
        
    def testTrack(self):
        i = Item.objects.get(content_type=CT(Track), object_id=1)
        self.assertEqual(str(i), "Track: Outkast - The Train (feat. Scar & Sleepy Brown)")
        
class PhotosTest(TestCase):
    fixtures = ["photos.json"]     
    
    def setUp(self):
        settings.FLICKR_USERNAME = "jacobian"   

    def testPhotoItem(self):
        i = Item.objects.get(content_type=CT(Photo), object_id=1)
        self.assertEqual(i.url, "http://www.flickr.com/photos/jacobian/1/")
        
    def testImageURLs(self):
        p = Photo.objects.get(pk=1)
        self.assertEqual(p.image_url, "http://static.flickr.com/123/1_1234567890.jpg")
        self.assertEqual(p.square_url, "http://static.flickr.com/123/1_1234567890_s.jpg")
        self.assertEqual(p.thumbnail_url, "http://static.flickr.com/123/1_1234567890_t.jpg")
        self.assertEqual(p.small_url, "http://static.flickr.com/123/1_1234567890_m.jpg")
        self.assertEqual(p.large_url, "http://static.flickr.com/123/1_1234567890_b.jpg")
        self.assertEqual(p.original_url, "http://static.flickr.com/123/1_1234567890_o.jpg")
        
    def testRepublishRights(self):
        mine, cc_by, cc_no, cc_nc_nd, cc_sa = Photo.objects.order_by("photo_id")
        self.assertEqual(mine.can_republish, True)
        self.assertEqual(cc_by.can_republish, True)
        self.assertEqual(cc_no.can_republish, False)
        self.assertEqual(cc_nc_nd.can_republish, True)
        self.assertEqual(cc_sa.can_republish, True)

    def testDerivativeRights(self):
        mine, cc_by, cc_no, cc_nc_nd, cc_sa = Photo.objects.order_by("photo_id")
        self.assertEqual(mine.derivative_ok, True)
        self.assertEqual(cc_by.derivative_ok, True)
        self.assertEqual(cc_no.derivative_ok, False)
        self.assertEqual(cc_nc_nd.derivative_ok, False)
        self.assertEqual(cc_sa.derivative_ok, True)

    def testShareAlikeRights(self):
        mine, cc_by, cc_no, cc_nc_nd, cc_sa = Photo.objects.order_by("photo_id")
        self.assertEqual(mine.must_share_alike, False)
        self.assertEqual(cc_by.must_share_alike, False)
        self.assertEqual(cc_no.must_share_alike, False)
        self.assertEqual(cc_nc_nd.must_share_alike, False)
        self.assertEqual(cc_sa.must_share_alike, True)
        
    def testCommercialRepublishRights(self):
        cc_nc_nd = Photo.objects.get(pk=4)
        saved, settings.SITE_IS_COMMERCIAL = getattr(settings, 'SITE_IS_COMMERCIAL', False), True
        self.assertEqual(cc_nc_nd.can_republish, False)
        settings.SITE_IS_COMMERCIAL = saved
        
    def testEXIF(self):
        p = Photo.objects.get(pk=1)
        self.assertEqual(p.exif, {})
        p.exif = {"Make" : "Nokia 6682", "Aperture" : "f/3.2"}
        p.save()
        p = Photo.objects.get(pk=1)
        self.assertEqual(p.exif, {"Make" : "Nokia 6682", "Aperture" : "f/3.2"})
        
class CodeCommitTest(TestCase):
    fixtures = ["codecommits.json"]
            
    def testCommit(self):
        c = CodeCommit.objects.get(pk=1)
        self.assertEqual(c.url, "http://code.djangoproject.com/changeset/42")
        
class WebSearchTest(TestCase):
    fixtures = ["websearches.json"]
    
    def testSearch(self):
        s = WebSearch.objects.get(pk=1)
        self.assertEqual(s.url, "http://www.google.com/search?q=test")
        
    def testResults(self):
        s = WebSearch.objects.get(pk=1)
        self.assertEqual(s.results.all()[0].url, "http://www.test.com/")
        
class VideoTest(TestCase):
    fixtures = ["videos.json"]
    
    def testGoogle(self):
        v = Video.objects.get(pk=1)
        self.assertEqual(v.embed_url, "http://video.google.com/googleplayer.swf?docId=-1182786924290841590&hl=en")
        
    def testYouTube(self):
        v = Video.objects.get(pk=2)
        self.assertEqual(v.embed_url, "http://www.youtube.com/v/1gvGDsIYrrQ")
        
class ItemTest(TestCase):
    fixtures = ["bookmarks.json", "photos.json", "trac.json", "tracks.json", "videos.json", "websearches.json"]
    
    def testSorting(self):
        items = list(Item.objects.all())
        self.assertEqual(items, sorted(items, reverse=True))
        
    def testModelsByName(self):
        self.assertEqual(Item.objects.models_by_name["bookmark"], Bookmark)
        self.assertEqual(Item.objects.models_by_name["codecommit"], CodeCommit)
        self.assertEqual(Item.objects.models_by_name["photo"], Photo)
        self.assertEqual(Item.objects.models_by_name["track"], Track)
        self.assertEqual(Item.objects.models_by_name["video"], Video)
        self.assertEqual(Item.objects.models_by_name["websearch"], WebSearch)
        
