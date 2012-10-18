import requests
import unittest
from flask_app import app

class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.app = app.app.test_client()
    def set_config(self, config, key, value):
        orig_value = getattr(config, key)
        setattr(config, key, value)
        self.addCleanup(setattr, config, key, orig_value)
