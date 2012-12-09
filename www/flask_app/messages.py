import logging
from bson import ObjectId
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
            logging.debug("Skipping recipient: %s", rcptto)
            continue
        message_file_id = get_message_fs().put(data)
        assert get_message_fs().get(message_file_id)
        _associate_file_with_mailbox(message_file_id, rcptto)
        messages.save({
                "mailbox_name":rcptto,
                "mail_from" : mailfrom,
                "sent_from" : peer,
                "recipients" : rcpttos,
                "file_id":message_file_id,
                })

def _associate_file_with_mailbox(message_file_id, mailbox_name):
    get_message_fs_files_collection().update({"_id":message_file_id}, {"$set" : {"mailbox_name" : mailbox_name}}, multi=True)
    get_message_fs_chunks_collection().update({"file_id":message_file_id}, {"$set" : {"mailbox_name" : mailbox_name}}, multi=True)
def delete_messages_by_mailbox(mailbox_name):
    for collection in (get_message_collection(), get_message_fs_chunks_collection(), get_message_fs_files_collection()):
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
        message_dict["message"] = get_message_fs().get(ObjectId(message_dict.pop("file_id"))).read()
        returned_ids.append(message_dict.pop("_id"))
        returned.append(message_dict)
    get_message_collection().update({"_id" : {"$in" : returned_ids}}, {"$set" : {"read" : True}}, multi=True)
    return returned
