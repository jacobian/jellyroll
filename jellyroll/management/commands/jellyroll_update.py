import logging
import optparse
import jellyroll.providers
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option(
            '-v', '--verbosity', 
            action='store', 
            dest='verbosity', 
            default='1',
            type='choice', 
            choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'
        ),
        optparse.make_option(
            "-p", "--provider", 
            dest="providers", 
            action="append", 
            help="Only use certain provider(s)."
        ),
        optparse.make_option(
            "-l", "--list-providers", 
            action="store_true", 
            help="Display a list of active data providers."
        ),
    )
    
    def handle(self, *args, **options):
        level = {'0': logging.WARN, '1': logging.INFO, '2': logging.DEBUG}[options['verbosity']]
        logging.basicConfig(level=level, format="%(name)s: %(levelname)s: %(message)s")

        if options['list_providers']:
            self.print_providers()
            return 0

        if options['providers']:
            for provider in options['providers']:
                if provider not in self.available_providers():
                    print "Invalid provider: %r" % provider
                    self.print_providers()
                    return 0

        jellyroll.providers.update(options['providers'])

    def available_providers(self):
        return jellyroll.providers.active_providers()

    def print_providers(self):
        available = sorted(self.available_providers().keys())
        print "Available data providers:"
        for provider in available:
            print "   ", provider
        