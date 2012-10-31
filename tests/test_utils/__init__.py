import requests
import unittest
from flask_app import app
from config import configobj

class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.app = app.app.test_client()
        configobj.backup()
    def tearDown(self):
        configobj.restore()
        super(TestCase, self).setUp()
