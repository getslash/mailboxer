from .test_utils import TestCase
from flask_app import config

class SanityTest(TestCase):
    def setUp(self):
        super(SanityTest, self).setUp()
        self.set_config(config.app, "REQUIRE_LOGIN", True)
    def test__index_page(self):
        rv = self.app.get("/")
        self.assertEquals(rv.status_code, 200)

