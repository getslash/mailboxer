from functools import wraps
from pymongo.helpers import AutoReconnect
import time
import types

def wrap_pymongo_connection(conn, sleep=time.sleep):
    conn.safe = True
    return AutoReconnectingConnection(conn, sleep=sleep)

class AutoReconnectingConnection(object):
    def __init__(self, conn, sleep):
        super(AutoReconnectingConnection, self).__init__()
        self._conn = conn
        self._sleep = sleep
    def __getattr__(self, attr):
        if attr.startswith("_") or not hasattr(self._conn, attr):
            raise AttributeError(attr)
        value = getattr(self._conn, attr)
        if isinstance(value, types.FunctionType) or isinstance(value, types.MethodType):
            return _wrap_autoreconnect_method(value, self._sleep)
        return value

def _wrap_autoreconnect_method(func, sleep):
    @wraps(func)
    def _callable(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except AutoReconnect:
                sleep(1)
    return _callable
