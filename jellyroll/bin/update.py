#!/usr/bin/env python

import sys
import logging
import optparse
import jellyroll.providers

def main(argv):
    parser = optparse.OptionParser()
    parser.add_option("-v", "--verbose", dest="level", action="store_const", const=logging.DEBUG, default=logging.INFO)
    parser.add_option("-q", "--quiet",   dest="level", action="store_const", const=logging.WARN,  default=logging.INFO)
    parser.add_option("-p", "--provider", dest="providers", action="append", help="Only use certain provider(s).")
    parser.add_option("-l", "--list-providers", action="store_true", help="Display a list of active data providers.")
    options, args = parser.parse_args(argv)

    logging.basicConfig(level=options.level, format="%(name)s: %(levelname)s: %(message)s")
    
    available_providers = jellyroll.providers.active_providers()
    
    if options.list_providers:
        print_providers(available_providers)
        sys.exit(0)
    
    if options.providers:
        for provider in options.providers:
            if provider not in available_providers:
                print "Invalid provider: %r" % provider
                print_providers(available_providers)
                sys.exit(0)
    
    jellyroll.providers.update(options.providers)

def print_providers(pl):
    print "Available data providers:"
    for provider in pl:
        print "   ", provider

if __name__ == '__main__':
    main(sys.argv)