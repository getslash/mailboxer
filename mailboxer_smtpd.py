# -*- coding: utf-8 -*-

#!/usr/bin/env python
import argparse
import asyncore
import email.parser
import logging
import smtpd
import sys

import gevent
import gevent.monkey
gevent.monkey.patch_select()

from flask_app import messages

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument('-v', action='append_const', const=1, dest='verbosity', default=[],
                    help="Be more verbose. Can be specified multiple times to increase verbosity further")
parser.add_argument("-p", "--port", default=25, type=int)

_parse_email_str = email.parser.Parser().parsestr

def main(args):
    server = SMTPServer(("0.0.0.0", args.port), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        logging.info('Finished')
    return 0

class SMTPServer(smtpd.SMTPServer, object):
    def process_message(self, peer, mailfrom, rcpttos, data):
        subject = _parse_email_str(data)['subject']
        logging.debug("Got message: %s", dict(to=rcpttos, sender=mailfrom, subject=subject, body=data))
        messages.process_message(peer, mailfrom, rcpttos, data)

################################## Boilerplate ################################
def _configure_logging(args):
    verbosity_level = len(args.verbosity)
    if verbosity_level == 0:
        level = 'WARNING'
    elif verbosity_level == 1:
        level = 'INFO'
    else:
        level = 'DEBUG'
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format='%(asctime)s -- %(message)s'
        )


#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    _configure_logging(args)
    sys.exit(main(args))


if __name__ == '__main__':
    main_entry_point()

################################################################################
