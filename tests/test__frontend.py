from .test_utils import TestCase

class SanityTest(TestCase):
    def setUp(self):
        super(SanityTest, self).setUp()
    def test__index_page(self):
        rv = self.app.get("/")
        self.assertEquals(rv.status_code, 200)

