from __future__ import with_statement

import mock
import datetime
import unittest
from django.conf import settings
from django.test import TestCase
from jellyroll.models import Item, Photo
from jellyroll.providers import flickr, utils

class FlickrClientTests(unittest.TestCase):
    
    def test_client_getattr(self):
        c = flickr.FlickrClient('apikey')
        self.assertEqual(c.api_key, 'apikey')
        self.assertEqual(c.method, 'flickr')
        
        c2 = c.foo.bar.baz
        self.assertEqual(c2.api_key, 'apikey')
        self.assertEqual(c2.method, 'flickr.foo.bar.baz')
    
    def test_client_call(self):
        mock_getjson = mock.Mock(return_value={})
        with mock.patch_object(utils, 'getjson', mock_getjson) as mocked:
            c = flickr.FlickrClient('apikey')
            res = c.foo.bar(a=1, b=2)
            self.assert_(mocked.called)
        
    def test_client_call_fail(self):
        failure = {'stat': 'fail', 'code': 1, 'message': 'fail'}
        mock_getjson = mock.Mock(return_value=failure)
        with mock.patch_object(utils, 'getjson', mock_getjson):
            c = flickr.FlickrClient('apikey')
            self.assertRaises(flickr.FlickrError, c.foo)

#
# Mock Flickr client
#

FakeClient = mock.Mock()
FakeClient.return_value = FakeClient

FakeClient.photos.licenses.getInfo.return_value = {
    'licenses': {
        "license": [{'id':'1', 'name':'All Rights Reserved', 'url':''}]
    }
}

FakeClient.people.getPublicPhotos.return_value = {
    'photos': {
        'page': 1,
        'pages': 1,
        'perpage': 500,
        'total': 1,
        'photo': [{
            "id":"3743398102",
            "owner":"81931330@N00",
            "secret":"2be7a25bfb",
            "server":"2589",
            "farm":3,
            "title":"Burrito",
            "ispublic":1,
            "isfriend":0,
            "isfamily":0,
            "license":"1",
            "datetaken":"2009-07-21 11:45:06", 
            "datetakengranularity":"0"}
        ]
    }
}

FakeClient.photos.getInfo.return_value = {
    "photo": {
        "id":"3743398102",
        "secret":"2be7a25bfb",
        "server":"2589",
        "farm":3,
        "dateuploaded":"1248194706",
        "isfavorite":0,
        "license":"1",
        "rotation":0,
        "originalsecret":"fef2098658",
        "originalformat":"jpg",
        "owner": {
            "nsid":"81931330@N00",
            "username":"jacobian",
            "realname":"Jacob Kaplan-Moss",
            "location":"Lawrence, KS"
        },
        "comments":{"_content":"0"},
        "title": {"_content":"Burrito"},
        "description": {"_content":"<i>This<\/i> is why I miss living in California!"},
        "dates": {
            "posted":"1248194706",
            "taken":"2009-07-21 11:45:06",
            "takengranularity":"0",
            "lastupdate":"1248194900"
        },
        "tags":{
            "tag":[
                {"id":"68660-3685776514-10052",
                 "author":"81931330@N00",
                 "raw":"burrito",
                 "_content":"burrito",
                 "machine_tag":0}
             ]
        },
        "urls":{
            "url":[
                {"type":"photopage", 
                 "_content":"http:\/\/www.flickr.com\/photos\/jacobian\/3743398102\/"}
            ]
        },
        "media":"photo"
    },
    "stat":"ok"
}

FakeClient.photos.getExif.return_value = {
    "photo": {
        "id":"3743398102",
        "secret":"2be7a25bfb",
        "server":"2589",
        "farm":3,
        "exif":[
            {"tagspace":"File",
             "tagspaceid":0,
             "tag":"FileSize",
             "label":"File Size",
             "raw":{"_content":"381 kB"}}
        ]
    }
}

class FlickrProviderTests(TestCase):
    
    def test_enabled(self):
        self.assertEqual(flickr.enabled(), True)
        
    @mock.patch_object(flickr, 'FlickrClient', FakeClient)
    def test_update(self):
        flickr.update()

        FakeClient.assert_called_with(settings.FLICKR_API_KEY)
        FakeClient.photos.licenses.getInfo.assert_called_with()
        FakeClient.people.getPublicPhotos.assert_called_with(
            user_id = settings.FLICKR_USER_ID,
            extras = "license,date_taken",
            per_page = "500",
            page = "2"
        )
        FakeClient.photos.getInfo.assert_called_with(photo_id=3743398102,
                                                     secret="2be7a25bfb")
        
        FakeClient.photos.getExif.assert_called_with(photo_id=3743398102,
                                                     secret="2be7a25bfb")
        
        # Check that the bookmark exists
        p = Photo.objects.get(pk="3743398102")
        self.assertEqual(p.server_id, 2589)
        self.assertEqual(p.farm_id, 3)
        self.assertEqual(p.secret, "2be7a25bfb")
        self.assertEqual(p.taken_by, "jacobian")
        self.assertEqual(p.cc_license, "")
        self.assertEqual(p.title, "Burrito")
        self.assertEqual(p.description, "<i>This<\/i> is why I miss living in California!")
        self.assertEqual(p.comment_count, 0)
        
        # Check that the Item exists
        i = Item.objects.get(content_type__model='photo', object_id=p.pk)
        self.assertEqual(i.timestamp.date(), datetime.date(2009, 7, 21))
        self.assertEqual(i.tags, 'burrito')
    

