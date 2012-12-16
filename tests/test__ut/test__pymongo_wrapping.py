from pymongo.helpers import AutoReconnect
from ..test_utils import TestCase
from flask_app.utils.pymongo_wrapper import wrap_pymongo_connection

class PymongoConnectionWrappingTest(TestCase):
    def setUp(self):
        super(PymongoConnectionWrappingTest, self).setUp()
        self.real_conn = ConnectionMock()
        self.assertFalse(self.real_conn.safe)
        self.conn = wrap_pymongo_connection(self.real_conn, sleep=self.sleep)
        self._sleeps = []
    def sleep(self, seconds):
        self._sleeps.append(seconds)
    def test__getattr(self):
        for attr in ("_fd", "x"):
            with self.assertRaises(AttributeError):
                getattr(self.conn, attr)
    def test__connection_is_safe(self):
        self.assertTrue(self.real_conn.safe)
    def test__method(self):
        num_errors = self.real_conn.counter = 5
        args = (1, 2, 3)
        kwargs = {"a" : 1, "b" : 2}
        self.assertEquals(self.conn.echo_method(*args, **kwargs), (args, kwargs))
        self.assertEquals(self.real_conn.counter, 0)
        self.assertEquals(self._sleeps, [1] * num_errors)

class ConnectionMock(object):
    safe = False
    counter = 0
    def echo_method(self, *args, **kwargs):
        if self.counter > 0:
            self.counter -= 1
            raise AutoReconnect()
        return args, kwargs
