import mongokit
from . import config

_connection = mongokit.Connection(config.app.DATABASE_HOST, safe=True)

def get_connection():
    return _connection

#################################### models ####################################
# @_connection.register
# class User(mongokit.Document):
#     structure = {
#         "email" : unicode,
#     }
#     indexes = [
#         {
#             "fields" : ["email"],
#             "unique" : True,
#         }
#     ]

