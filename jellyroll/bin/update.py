import sys
import logging
from django.conf import settings

def update_all():
    log = logging.getLogger("jellyroll.updater")
    log.info("Updating from all data providers")
    
    for provider in settings.JELLYROLL_PROVIDERS:
        log.debug("Importing %r", provider)
        try:
            mod = __import__(provider, '', '', [''])
        except ImportError, e:
            log.error("Couldn't import %r: %s" % (provider, e))
            continue
            
        if not mod.enabled():
            log.info("Skipping %r: enabled() returned False", provider)
            continue
            
        if not mod.needs_update():
            log.info("Skipping %r: needs_update() returned False", provider)
            
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

if __name__ == '__main__':
    if "-v" in sys.argv:
        level = logging.DEBUG
    elif "-q" in sys.argv:
        level = logging.WARN
    else: 
        level = logging.INFO
    logging.basicConfig(level=level, format="%(name)s: %(levelname)s: %(message)s")
    update_all()