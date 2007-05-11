from django import template
from django.test import TestCase
from jellyroll.models import *

class TagTestCase(TestCase):
    """Helper class with some tag helper functions"""
    
    def installTagLibrary(self, library):
        template.libraries[library] = __import__(library)
        
    def renderTemplate(self, tstr, **context):
        t = template.Template(tstr)
        c = template.Context(context)
        return t.render(c)

class RenderTagTest(TagTestCase):
    fixtures = ["videos.json"]
    
    def setUp(self):
        self.installTagLibrary('jellyroll.templatetags.jellyroll')
        
    def testRenderSimple(self):
        i = Item.objects.get(pk=1)
        o = self.renderTemplate("{% load jellyroll %}{% jellyrender i %}", i=i)
        self.assert_(o.startswith('<div class="jellyroll-item">'), o)
        
    def testRenderUsing(self):
        i = Item.objects.get(pk=1)
        o = self.renderTemplate('{% load jellyroll %}{% jellyrender i using "jellyroll/snippets/item.txt" %}', i=i)
        self.assertEqual(str(i.object), o)
        
    def testRenderAs(self):
        i = Item.objects.get(pk=1)
        o = self.renderTemplate('{% load jellyroll %}{% jellyrender i as o using "jellyroll/snippets/item.txt" %} -- {{ o }}', i=i)
        self.assertEqual(" -- %s" % str(i.object), o)

class GetJellyrollItemsTagSyntaxTest(TestCase):
    
    def getNode(self, str):
        from jellyroll.templatetags.jellyroll import get_jellyroll_items
        return get_jellyroll_items(None, template.Token(template.TOKEN_BLOCK, str))
        
    def assertNodeException(self, str):
        self.assertRaises(template.TemplateSyntaxError, self.getNode, str)
    
    def testLimit(self):
        node = self.getNode("get_jellyroll_items limit 10 as items")
        self.assertEqual(node.limit, 10)
        self.assertEqual(node.start, None)
        self.assertEqual(node.end, None)
        self.assertEqual(node.asvar, "items")
    
    def testBetween(self):
        node = self.getNode("get_jellyroll_items between '2007-01-01' and '2007-01-31' as items")
        self.assertEqual(node.limit, None)
        self.assertEqual(node.start, "'2007-01-01'")
        self.assertEqual(node.end, "'2007-01-31'")
        
    def testReversed(self):
        node = self.getNode("get_jellyroll_items limit 10 reversed as items")
        self.assertEqual(node.reversed, True)
    
    def testOfType(self):
        node = self.getNode("get_jellyroll_items oftype video limit 10 as items")
        self.assertEqual(node.oftypes, [Video])

    def testOfTypes(self):
        node = self.getNode("get_jellyroll_items oftype video oftype photo limit 10 as items")
        self.assertEqual(node.oftypes, [Video, Photo])

    def testExcludeType(self):
        node = self.getNode("get_jellyroll_items excludetype video limit 10 as items")
        self.assertEqual(node.excludetypes, [Video])

    def testExcludeTypes(self):
        node = self.getNode("get_jellyroll_items excludetype video excludetype photo limit 10 as items")
        self.assertEqual(node.excludetypes, [Video, Photo])

    def testInvalidSyntax(self):
        self.assertNodeException("get_jellyroll_items")
        self.assertNodeException("get_jellyroll_items as")
        self.assertNodeException("get_jellyroll_items as items")
        self.assertNodeException("get_jellyroll_items limit")
        self.assertNodeException("get_jellyroll_items limit frog")
        self.assertNodeException("get_jellyroll_items between")
        self.assertNodeException("get_jellyroll_items between x")
        self.assertNodeException("get_jellyroll_items between x and")
        self.assertNodeException("get_jellyroll_items between x spam y")
        self.assertNodeException("get_jellyroll_items oftype")
        self.assertNodeException("get_jellyroll_items excludetype")
        
    def testInvalidTypes(self):
        self.assertNodeException("get_jellyroll_items limit 10 oftype frog as items")
        self.assertNodeException("get_jellyroll_items limit 10 excludetype frog as items")
        
class GetJellyrollItemsTagTest(TagTestCase):
    fixtures = ["bookmarks.json", "photos.json", "trac.json", "tracks.json", "videos.json", "websearches.json"]

    def setUp(self):
        self.installTagLibrary('jellyroll.templatetags.jellyroll')

    def testLimit(self):
        o = self.renderTemplate("{% load jellyroll %}"\
                                "{% get_jellyroll_items limit 5 as items %}"\
                                "{{ items|length }}")
        self.assertEqual(o, "5")
        
    def testBetween1(self):
        o = self.renderTemplate("{% load jellyroll %}"\
                                "{% get_jellyroll_items between '2006' and 'now' as items %}"\
                                "{{ items|length }}")
        self.assertEqual(o, "10")
        
    def testBetween2(self):
        o = self.renderTemplate("{% load jellyroll %}"\
                                "{% get_jellyroll_items between '2001' and '2002' as items %}"\
                                "{{ items|length }}")
        self.assertEqual(o, "0")

    def testReversed(self):
        t1 = "{% load jellyroll %}"\
             "{% get_jellyroll_items limit 10 as forwards %}"\
             "{{ forwards.0.id }}"
        t2 = "{% load jellyroll %}"\
             "{% get_jellyroll_items limit 10 reversed as backwards %}"\
             "{{ backwards.9.id }}"
        self.assertEqual(self.renderTemplate(t1), self.renderTemplate(t2))
        
    def testOfType(self):
        o = self.renderTemplate("{% load jellyroll %}"\
                                "{% get_jellyroll_items oftype photo limit 10 as items %}"\
                                "{{ items|length }}")
        self.assertEqual(o, "5")
        
    def testOfTypes(self):
        o = self.renderTemplate("{% load jellyroll %}"\
                                "{% get_jellyroll_items oftype photo oftype video limit 10 as items %}"\
                                "{{ items|length }}")
        self.assertEqual(o, "7")

    def testExcludeType(self):
        o = self.renderTemplate("{% load jellyroll %}"\
                                "{% get_jellyroll_items excludetype photo limit 10 as items %}"\
                                "{{ items|length }}")
        self.assertEqual(o, "5")

    def testExcludeTypes(self):
        o = self.renderTemplate("{% load jellyroll %}"\
                                "{% get_jellyroll_items excludetype photo excludetype video limit 10 as items %}"\
                                "{{ items|length }}")
        self.assertEqual(o, "3")
