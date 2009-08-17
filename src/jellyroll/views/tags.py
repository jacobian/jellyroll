"""
Views for looking at Jellyroll items by tag.

"""

from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.contenttypes.models import ContentType
from django.views.generic.list_detail import object_list
from django.template import RequestContext
from django.http import Http404
from jellyroll.models import Item
from tagging.models import TaggedItem, Tag


def tag_list(request):
    #tags = sorted( Tag.objects.usage_for_model(Item),
    #               cmp=lambda x,y: cmp(x.name.lower(),y.name.lower()) )
    item_ct = ContentType.objects.get_for_model(Item)
    tag_items = TaggedItem.objects.filter(content_type=item_ct)
    tags = Tag.objects.filter(pk__in=[ tag_item.tag.pk for tag_item in tag_items ])
    return object_list(request, tags, template_object_name='tag',
                       template_name='jellyroll/tags/tag_list.html')

def tag_item_list(request, tag):
    tag = get_object_or_404(Tag,name=tag)
    items = TaggedItem.objects.get_by_model(Item,tag)
    return object_list(request, items, template_object_name='item',
                       template_name='jellyroll/tags/tag_item_list.html', 
                       extra_context={'tag':tag})
