import md5
import datetime
import logging
import dateutil
import re
from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import slugify
from django.utils.functional import memoize
from django.utils.http import urlquote
from django.utils.encoding import smart_str, smart_unicode
from httplib2 import HttpLib2Error
from jellyroll.providers import utils
from jellyroll.models import Item, Message, ContentLink


#
# API URLs
#

RECENT_STATUSES_URL = "http://twitter.com/statuses/user_timeline/%s.rss"
USER_URL = "http://twitter.com/%s"

#
# Public API
#

log = logging.getLogger("jellyroll.providers.twitter")

def enabled():
    return True

def update():
    last_update_date = Item.objects.get_last_update_of_model(Message)
    log.debug("Last update date: %s", last_update_date)
    
    xml = utils.getxml(RECENT_STATUSES_URL % settings.TWITTER_USERNAME)
    for status in xml.getiterator("item"):
        message      = status.find('title')
        message_text = smart_unicode(message.text)
        url          = smart_unicode(status.find('link').text)

        # pubDate delivered as UTC
        timestamp    = dateutil.parser.parse(status.find('pubDate').text)
        if utils.JELLYROLL_ADJUST_DATETIME:
            timestamp = utils.utc_to_local_datetime(timestamp)

        if not _status_exists(message_text, url, timestamp):
            _handle_status(message_text, url, timestamp)

#
# GLOBAL CLUTTER
#

TWITTER_TRANSFORM_MSG = False
TWITTER_RETWEET_TXT = "Forwarding from %s: "
try:
    TWITTER_TRANSFORM_MSG = settings.TWITTER_TRANSFORM_MSG
    TWITTER_RETWEET_TXT = settings.TWITTER_RETWEET_TXT
except AttributeError:
    pass

if TWITTER_TRANSFORM_MSG:
    USER_LINK_TPL = '<a href="%s" title="%s">%s</a>'
    TAG_RE = re.compile(r'(?P<tag>\#\w+)')
    USER_RE = re.compile(r'(?P<username>@\w+)')
    RT_RE = re.compile(r'RT\s+(?P<username>@\w+)')
    USERNAME_RE = re.compile(r'^%s:'%settings.TWITTER_USERNAME)

    # modified from django.forms.fields.url_re
    URL_RE = re.compile(
        r'https?://'
        r'(?:(?:[A-Z0-9-]+\.)+[A-Z]{2,6}|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/\S+|/?)', re.IGNORECASE)

    def _transform_retweet(matchobj):
        if '%s' in TWITTER_RETWEET_TXT:
            return TWITTER_RETWEET_TXT % matchobj.group('username')
        return TWITTER_RETWEET_TXT

    def _transform_user_ref_to_link(matchobj):
        user = matchobj.group('username')[1:]
        link = USER_URL % user
        return USER_LINK_TPL % \
            (link,user,''.join(['@',user]))

    def _parse_message(message_text):
        """
        Parse out some semantics for teh lulz.
        
        """
        links = list()
        tags = ""

        # remove newlines
        message_text = message_text.replace('\n','')
        # generate link list for ContentLink
        links = [ link for link in URL_RE.findall(message_text) ]
        link_ctr = 1
        link_dict = {}
        for link in URL_RE.finditer(message_text):
            link_dict[link.group(0)] = link_ctr
            link_ctr += 1
        generate_link_num = lambda obj: "[%d]"%link_dict[obj.group(0)]
        # remove URLs referenced in message content
        if not hasattr(settings, 'TWITTER_REMOVE_LINKS') or settings.TWITTER_REMOVE_LINKS == True:
        	message_text = URL_RE.sub(generate_link_num,message_text)
        # remove leading username
        message_text = USERNAME_RE.sub('',message_text)
        # check for RT-type retweet syntax
        message_text = RT_RE.sub(_transform_retweet,message_text)
        # replace @user references with links to their timeline
        message_text = USER_RE.sub(_transform_user_ref_to_link,message_text)
        # generate tags list
        tags = ' '.join( [tag[1:] for tag in TAG_RE.findall(message_text)] )
        # extract defacto #tag style tweet tags
        if not hasattr(settings, 'TWITTER_REMOVE_TAGS') or settings.TWITTER_REMOVE_TAGS == True:
            message_text = TAG_RE.sub('',message_text)

        return (message_text.strip(),links,tags)

    log.info("Enabling message transforms")
else:
    _parse_message = lambda msg: (msg,list(),"")
    log.info("Disabling message transforms")

#
# Private API
#

@transaction.commit_on_success
def _handle_status(message_text, url, timestamp):
    message_text, links, tags = _parse_message(message_text)

    t = Message(
        message = message_text,
        )

    if not _status_exists(message_text, url, timestamp):
        log.debug("Saving message: %r", message_text)
        item = Item.objects.create_or_update(
            instance = t,
            timestamp = timestamp,
            source = __name__,
            source_id = _source_id(message_text, url, timestamp),
            url = url,
            tags = tags,
            )
        item.save()

        for link in links:
            l = ContentLink(
                url = link,
                identifier = link,
                )
            l.save()
            t.links.add(l)

def _source_id(message_text, url, timestamp):
    return md5.new(smart_str(message_text) + smart_str(url) + str(timestamp)).hexdigest()
    
def _status_exists(message_text, url, timestamp):
    id = _source_id(message_text, url, timestamp)
    try:
        Item.objects.get(source=__name__, source_id=id)
    except Item.DoesNotExist:
        return False
    else:
        return True
