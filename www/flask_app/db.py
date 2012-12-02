from flask.ext import mongokit as flask_mongokit
from .utils.pymongo_wrapper import wrap_pymongo_connection

class AutoclaveMongoKit(flask_mongokit.MongoKit):
    def connect(self):
        super(AutoclaveMongoKit, self).connect()
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

