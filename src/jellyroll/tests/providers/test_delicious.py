import mock
import datetime
import unittest
from django.conf import settings
from django.test import TestCase
from jellyroll.models import Item, Bookmark
from jellyroll.providers import delicious
from jellyroll.providers.utils.anyetree import etree

class DeliciousClientTests(unittest.TestCase):
    
    def test_client_getattr(self):
        c = delicious.DeliciousClient('username', 'password')
        self.assertEqual(c.username, 'username')
        self.assertEqual(c.password, 'password')
        self.assertEqual(c.method, 'v1')
        
        c2 = c.foo.bar.baz
        self.assertEqual(c2.username, 'username')
        self.assertEqual(c2.password, 'password')
        self.assertEqual(c2.method, 'v1/foo/bar/baz')
        
    @mock.patch('jellyroll.providers.utils.getxml')
    def test_client_call(self, mocked):
        c = delicious.DeliciousClient('username', 'password')
        res = c.foo.bar(a=1, b=2)
        
        mocked.assert_called_with(
            'https://api.del.icio.us/v1/foo/bar?a=1&b=2',
            username = 'username',
            password = 'password'
        )

#    
# Fake delicious client that mocks all the calls update() makes.
#

# Quick 'n' dirty XML etree maker
xml = lambda s: etree.fromstring(s.strip())

FakeClient = mock.Mock()

# This makes FakeClient.__init__ do the right thing w/r/t mocking
FakeClient.return_value = FakeClient

FakeClient.posts.update.return_value = xml(
    '<update time="2009-08-18T15:30:16Z" inboxnew="0"/>'
)

FakeClient.posts.dates.return_value = xml('''
    <dates tag="" user="jellyroll">
        <date count="1" date="2009-08-18"/>
    </dates>
''')

FakeClient.posts.get.return_value = xml('''
    <posts user="jellyroll" dt="2009-08-18T15:30:16Z">
        <post href="http://jacobian.org/"
              hash="151ebb66839faa8ed073b27fb897b166"
              description="Me!"
              time="2009-08-18T15:30:16Z"
              extended="I'm awesome."
              tag="me jacob jacobian"
        />
    </posts>
''')

class DeliciousProviderTests(TestCase):
    
    def test_enabled(self):
        self.assertEqual(delicious.enabled(), True)
        
    @mock.patch_object(delicious, 'DeliciousClient', FakeClient)
    def test_update(self):
        delicious.update()
        
        # Check that the calls to the API match what we expect
        FakeClient.assert_called_with(settings.DELICIOUS_USERNAME, settings.DELICIOUS_PASSWORD)
        FakeClient.posts.update.assert_called_with()
        FakeClient.posts.dates.assert_called_with()
        FakeClient.posts.get.assert_called_with(dt='2009-08-18')
        
        # Check that the bookmark exists
        b = Bookmark.objects.get(url="http://jacobian.org/")
        self.assertEqual(b.description, "Me!")
        
        # Check that the Item exists
        i = Item.objects.get(content_type__model='bookmark', object_id=b.pk)
        self.assertEqual(i.timestamp.date(), datetime.date(2009, 8, 18))
        self.assertEqual(i.tags, 'me jacob jacobian')
    
    @mock.patch_object(delicious, 'DeliciousClient', FakeClient)
    @mock.patch_object(delicious, 'log')
    def test_update_skipped_second_time(self, mocked):
        delicious.update()
        delicious.update()
        self.assert_(mocked.info.called)
