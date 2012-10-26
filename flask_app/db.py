from flask.ext.mongokit import MongoKit, Document
from . import config

db = MongoKit()

#################################### models ####################################
# @db.register
# class User(mongokit.Document):
#     __collection__ = "users"
#     structure = {
#         "email" : unicode,
#     }
#     indexes = [
#         {
#             "fields" : ["email"],
#             "unique" : True,
#         }
#     ]

