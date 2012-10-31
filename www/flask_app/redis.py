from __future__ import absolute_import
import redis

def get_connection(db=0):
    return redis.StrictRedis()
