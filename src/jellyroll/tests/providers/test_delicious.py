import mock
import unittest
from django.conf import settings
from django.test import TestCase
from jellyroll.providers import delicious

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
    
class DeliciousProviderTests(TestCase):
    
    def test_enabled(self):
        self.assertEqual(delicious.enabled(), True)