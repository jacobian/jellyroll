import logging
from django.conf import settings

try:
    set
except NameError:
    from sets import Set as set     # Python 2.3 fallback

log = logging.getLogger("jellyroll.update")

def active_providers():
    """
    Return a dict of {name: module} of active, enabled providers.
    """
    providers = {}
    for provider in settings.JELLYROLL_PROVIDERS:
        try:
            mod = __import__(provider, '', '', [''])
        except ImportError, e:
            log.error("Couldn't import provider %r: %s" % (provider, e))
            raise
        if mod.enabled():
            providers[provider] = mod
    return providers
    
def update(providers):
    """
    Update a given set of providers. If the list is empty, it means update all
    of 'em.
    """
    active = active_providers()
    if providers is None:
        providers = active.keys()
        
    for provider in providers:
        log.debug("Updating from provider %r", provider)
        try:
            mod = active[provider]
        except KeyError:
            log.error("Unknown provider: %r" % provider)
            continue

        log.info("Running '%s.update()'", provider)
        try:
            mod.update()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            log.error("Failed during '%s.update()'", provider)
            log.exception(e)
            continue

        log.info("Done with provider %r", provider)
