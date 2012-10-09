import logging
from .db import (
    get_mailbox_collection,
    get_message_collection,
    get_message_fs,
    get_message_fs_files_collection,
    get_message_fs_chunks_collection,
    )

def process_message(peer, mailfrom, rcpttos, data):
    mailboxes = get_mailbox_collection()
    messages = get_message_collection()
    logging.debug("Processing message from %s", mailfrom)
    for rcptto in rcpttos:
        if mailboxes.find({"name":rcptto}).count() == 0:
            continue
        with get_message_fs().new_file() as message_file:
            message_file.write(data)
        _associate_file_with_mailbox(message_file, rcptto)
        messages.save({
                "mailbox_name":rcptto,
                "mail_from" : mailfrom,
                "sent_from" : peer,
                "recipients" : rcpttos,
                "file_id":message_file._id,
                })

def _associate_file_with_mailbox(message_file, mailbox_name):
    get_message_fs_files_collection().update({"_id":message_file._id}, {"$set" : {"mailbox_name" : mailbox_name}})
    get_message_fs_chunks_collection().update({"file_id":message_file._id}, {"$set" : {"mailbox_name" : mailbox_name}})
def delete_messages_by_mailbox(mailbox_name):
    for collection in (get_message_fs_chunks_collection(), get_message_fs_files_collection()):
        collection.remove({"mailbox_name" : mailbox_name})
def delete_all_messages():
    for collection in (get_message_fs_chunks_collection(), get_message_fs_files_collection()):
        collection.remove()

def get_messages(mailbox_name, include_read=True):
    returned = []
    returned_ids = []
    criteria = {"mailbox_name" : mailbox_name}
    if not include_read:
        criteria.update({"read" : {"$ne" : True}})
    for message in get_message_collection().find(criteria):
        message_dict = dict(message)
        message_dict["message"] = get_message_fs().get(message_dict.pop("file_id")).read()
        returned_ids.append(message_dict.pop("_id"))
        returned.append(message_dict)
    get_message_collection().update({"_id" : {"$in" : returned_ids}}, {"read" : True})
    return returned
