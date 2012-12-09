#! /usr/bin/python
from __future__ import print_function
import argparse
import logging
import os
import sys

from deployment import fix_paths

from config import config

from flask_app.app import app

parser = argparse.ArgumentParser(usage="%(prog)s [options] args...")

def main(args):
    _configure_logging()
    app.config["SECRET_KEY"] = "TESTING_SECRET_KEY"
    config.deployment.openid.storage_path = "/tmp/__debug_openid_store"
    app.run(debug=True, port=config.deployment.www.testing_frontend_port)
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
    sys.exit(main(parser.parse_args()))
if __name__ == '__main__':
    main_entry_point()

