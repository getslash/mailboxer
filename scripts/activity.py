#!/usr/bin/env python
import argparse
import collections
import itertools
import os
import random
import sys
import time
from contextlib import contextmanager

import logbook

sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))
from flask_app import app
from flask_app.smtp import smtpd_context
from mailboxer import Mailboxer


parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument("--smtp-port", default=None, type=int)
parser.add_argument("--port", default=8080)


class Application(object):
    def __init__(self, args):
        self._args = args

    def main(self):
        client = Mailboxer("http://127.0.0.1:{0}".format(self._args.port))
        mailboxes = collections.deque(maxlen=5)
        with self._get_smtpd_context() as smtp:
            for iteration in itertools.count():
                if iteration % 3 == 0:
                    logbook.info("Creating mailbox (#{})", iteration)
                    mailboxes.append("mailbox{0}@demo.com".format(time.time()))
                    client.create_mailbox(mailboxes[-1])
                logbook.info("Sending email... (#{})", iteration)
                smtp.sendmail("noreply@demo.com", [random.choice(mailboxes)], "This is message no. {0}".format(iteration))
                time.sleep(5)
        return 0

    @contextmanager
    def _get_smtpd_context(self):
        if self._args.smtp_port is None:
            with smtpd_context() as result:
                yield result
        else:
            yield SMTP("127.0.0.1", self._args.smtp_port)



#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    app = Application(args)
    sys.exit(app.main())


if __name__ == "__main__":
    main_entry_point()
