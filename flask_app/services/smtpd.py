#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import argparse
import asyncore
import email.parser
import logbook
import os
import smtpd
import sys

from .. import messages

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument('-v', action='append_const', const=1, dest='verbosity', default=[],
                    help="Be more verbose. Can be specified multiple times to increase verbosity further")
parser.add_argument("-p", "--port", default=25, type=int)
parser.add_argument("--secure", action="store_true", default=False)

def main(args):
    server = initialize_server(args.port, secure=args.secure)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        logbook.info('Finished')
    return 0

def initialize_server(port, secure):
    cls = SecureSMTPServer if secure else SMTPServer
    return cls(("0.0.0.0", port), None)

class SMTPServer(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data):
        logbook.debug("Processing message peer={} from={} to={}", peer, mailfrom, rcpttos)
        try:
            messages.process_incoming_message(messages.Context(peer), mailfrom, rcpttos, data)
        except:
            logbook.error("Exception while processing", exc_info=True)
            raise

#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    sys.exit(main(args))

if __name__ == '__main__':
    main_entry_point()
