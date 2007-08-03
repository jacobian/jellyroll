from django.test import TestCase
import jellyroll.utils

# XXX this isn't much of a test.

class TestHighlightCode(TestCase):
    def testHighlightCode(self):
        source = jellyroll.utils.highlight_code("def foo(): pass", language="python")