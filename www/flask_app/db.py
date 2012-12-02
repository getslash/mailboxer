from .utils.pymongo_wrapper import wrap_pymongo_connection
from flask.ext import mongokit as flask_mongokit
from pymongo.helpers import AutoReconnect
from time import sleep

class AutoclaveMongoKit(flask_mongokit.MongoKit):
    def connect(self):
        while True:
            try:
                super(AutoclaveMongoKit, self).connect()
            except AutoReconnect:
                sleep(1)
                continue
            else:
                break
        flask_mongokit.ctx_stack.top.mongokit_connection = wrap_pymongo_connection(
            flask_mongokit.ctx_stack.top.mongokit_connection
        )

db = AutoclaveMongoKit()

#################################### models ####################################
# @db.register
# class User(flask_mongokit.Document):
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

