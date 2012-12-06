import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "deployment"))
import fix_paths
import requests
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "www"))

from flask_app import app
from config import configobj

class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        configobj.backup()
        self.app = app.app.test_client()
        app.app.config["SECRET_KEY"] = "testing_key"
    def tearDown(self):
        configobj.restore()
        super(TestCase, self).setUp()
