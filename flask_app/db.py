import pymongo
from . import config
import gridfs

_connection = None

def get_connection():
    global _connection
    if _connection is None:
        _connection = pymongo.Connection(config.app.DATABASE_HOST, safe=True)
    return _connection

def get_mailbox_collection():
    return get_db()["mailboxes"]

def get_message_collection():
    return get_db()["messages"]

def get_db():
    return get_connection()["mailboxer"]

_MESSAGE_FS_NAME = "messages_fs"

def get_message_fs():
    return gridfs.GridFS(get_db(), _MESSAGE_FS_NAME)

def get_message_fs_files_collection():
    return get_db()["{}.files".format(_MESSAGE_FS_NAME)]
def get_message_fs_chunks_collection():
    return get_db()["{}.chunks".format(_MESSAGE_FS_NAME)]
