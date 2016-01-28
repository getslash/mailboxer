#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import argparse
import logbook
import sys
import socket
from contextlib import closing

from .. import app # needed to prevent cyclic dependency
from ..message_sink import DatabaseMessageSink
from ..smtp import SMTPServingThread

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument("-d", "--debug", default=False, action="store_true")
parser.add_argument("-p", "--port", default=25, type=int)

def main(args):
    if not args.debug:
        for handler in [logbook.SyslogHandler(level=logbook.INFO)]:
            handler.format_string = '{record.thread}|{record.channel}: {record.message}'
            handler.push_application()

    with closing(socket.socket()) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", args.port))
        logbook.debug("Listening on port {}", args.port)
        s.listen(socket.SOMAXCONN)
        message_sink = DatabaseMessageSink()
        while True:
            p, a = s.accept()
            logbook.debug("Incoming connection from {}", a)
            thread = SMTPServingThread(p, message_sink)
            thread.daemon = True
            thread.start()

#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    sys.exit(main(args))

if __name__ == '__main__':
    main_entry_point()
