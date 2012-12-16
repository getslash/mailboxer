import pymongo
import gridfs

_connection = None

def get_connection():
    global _connection
    if _connection is None:
        _connection = pymongo.Connection("127.0.0.1", safe=True)
        _ensure_indexes(_connection)
    return _connection

def _ensure_indexes(conn):
    get_message_collection(conn).ensure_index("id")

def get_mailbox_collection(conn=None):
    return get_db(conn)["mailboxes"]

def get_message_collection(conn=None):
    return get_db(conn)["messages"]

def get_db(conn=None):
    if conn is None:
        conn = get_connection()
    return conn["mailboxer"]

_MESSAGE_FS_NAME = "messages_fs"

def get_message_fs():
    return gridfs.GridFS(get_db(), _MESSAGE_FS_NAME)

def get_message_fs_files_collection():
    return get_db()["{}.files".format(_MESSAGE_FS_NAME)]
def get_message_fs_chunks_collection():
    return get_db()["{}.chunks".format(_MESSAGE_FS_NAME)]
