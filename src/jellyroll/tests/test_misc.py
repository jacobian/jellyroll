import unittest
import jellyroll.providers

class MiscTests(unittest.TestCase):
    def test_providers_expand_star(self):
        expanded = jellyroll.providers.expand_star("jellyroll.providers.*")
        self.assertEqual(expanded, [
            'jellyroll.providers.delicious',
            'jellyroll.providers.flickr',
            'jellyroll.providers.gitscm',
            'jellyroll.providers.gsearch',
            'jellyroll.providers.lastfm',
            'jellyroll.providers.svn',
            'jellyroll.providers.twitter',
            'jellyroll.providers.youtube',
        ])