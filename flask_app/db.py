import pymongo
from . import config

_connection = None

def get_connection(self):
    global _connection
    if _connection is None:
        _connection = pymongo.Connection(config.AUTOCLAVE_DATABASE_HOST, safe=True)
    return _connection
