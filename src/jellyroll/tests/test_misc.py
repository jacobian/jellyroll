import unittest
import jellyroll.providers

class MiscTests(unittest.TestCase):
    def test_providers_expand_star(self):
        expanded = jellyroll.providers.expand_star("jellyroll.providers.*")
        expected = [
            'jellyroll.providers.delicious',
            'jellyroll.providers.flickr',
            'jellyroll.providers.gitscm',
            'jellyroll.providers.gsearch',
            'jellyroll.providers.lastfm',
            'jellyroll.providers.latitude',
            'jellyroll.providers.svn',
            'jellyroll.providers.twitter',
            'jellyroll.providers.youtube',
        ]
        expanded.sort()
        expected.sort()
        self.assertEqual(expanded, expected)