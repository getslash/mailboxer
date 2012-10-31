#! /usr/bin/python
from __future__ import print_function
import argparse
import logging
import os
import sys

from flask_app.app import app
from config import config

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")
parser.add_argument("-d", "--debug", action="store_true", default=False)
parser.add_argument("-v", "--verbose", action="store_true", default=False)

def main(args):
    from gevent.wsgi import WSGIServer
    if args.debug:
        app.run(debug=True, port=config.deployment.www.testing_frontend_port)
    else:
        http_server = WSGIServer(("0.0.0.0", config.deployment.www.production_frontend_port), app)
        http_server.serve_forever()
    return 0

################################## Boilerplate #################################
def _configure_logging():
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="%(asctime)s -- %(message)s"
        )

#### For use with entry_points/console_scripts
def main_entry_point():
    args = parser.parse_args()
    if args.verbose:
        _configure_logging()
    sys.exit(main(args))
if __name__ == '__main__':
    main_entry_point()

