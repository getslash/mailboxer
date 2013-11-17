import sys
import os
import requests
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from flask_app import app
from flask_app import models

from .smtpd_utils import smtpd_context

class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.app = app.app.test_client()
        app.app.config["SECRET_KEY"] = "testing_key"
        models.db.session.close()
        models.db.drop_all()

        models.db.create_all()

