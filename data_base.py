"""
data_base.py: The Data Access Layer (DAL) of the project.

This module interacts with the MongoDB database and the Gmail API to fetch, process, and store email data. It provides functions to initialize, update, and manage the database.

Functions:
- init_db(email): Initializes the database with email data.
- make_db(email): Creates a new database for a user.
- update_db(email): Updates the database with new email data.
- purify_message(messages): Prepares email messages for database insertion.
"""
from constent import *
import shared_resources
import pymongo
from simplegmail import Gmail , message , label
from simplegmail.query import construct_query
import logging

logging.basicConfig(level=logging.INFO)
gmail = Gmail()


categories = ["CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS", "CATEGORY_PERSONAL", "CATEGORY_PRIMARY"]



def init_db(email) -> None:
    """
    Init the database with the user email data for the first time
    """
    db = shared_resources.client["Deft"]
    users_collection = db["Users"]
    message_collection = db["Messages"]
    labels = gmail.list_labels()
    for label in labels: 
        messages = gmail.get_messages(query=f"label: {label.name}")
        if messages != []:
            messages = purify_message(messages)
            message_collection.insert_many(messages)
            message_ids = [message['id'] for message in messages]
            users_collection.update_one({"email": email}, {"$push": {label.name: {"$each": message_ids}}})


def make_db(email) -> None:
    """
    Makes a documment for the user with the email 
    """
    email_name_of_user =shared_resources.get_name_from_email(email)
    db = shared_resources.client["Deft"]
    users_collection = db["Users"]
    
    user_data_set = users_collection.find_one({"name": email_name_of_user})
    if not user_data_set:
        labels = gmail.list_labels()
        label_lists = {label.name: [] for label in labels}
        users_collection.insert_one({"email": email, "name": email_name_of_user, **label_lists})


def update_db(email) -> None:
    """
    Get the messages from the user gmail account and check if there's a message that dosent exist in the collection
    by checking the id & labels of the message
    """
    db = shared_resources.client["Deft"]
    users_collection = db["Users"]
    message_collection = db["Messages"]
    labels = gmail.list_labels()
   
    for label in labels: #TODO: use faster data structure to contain the messages
        messages = gmail.get_messages(query=f"label: {label.name}")
        for msg in messages:
            found =  message_collection.count_documents({"id": msg.id, "label_ids": labels_to_list(msg.label_ids)})
            if not found:
                found2 = message_collection.find_one({"id": msg.id})
                if found2:
                    message_collection.delete_one({"id": msg.id})
                message_collection.insert_one(purify_message(msg))
                if any(label.name in categories for label in msg.label_ids):
                    category_handler(msg, label.name, email)


def category_handler(message, label, email)-> None:
    db = shared_resources.client["Deft"]
    user_collection = db["Users"]
    message = purify_message(message)
    user_collection.update_one({"email": email}, {"$push": {label: message["id"]}})


def labels_to_list(labels)-> list[str]: #TODO: change the isertion to the function 
    if isinstance(labels[0], label.Label):
        return [label.name for label in labels]
    elif isinstance(labels, str):
        return [label for label in labels]

def purify_message(messages) -> list[dict]:
    """
    Makes the messages list to be valid for mongoDB
    """
    fields = Constent.fields   
    if isinstance(messages, list):
        messages = [message.__dict__ for message in messages]  
        messages = [Constent.filter_fields(message, labels_to_list) for message in messages]  
   # if the messages is a single message, message is an object from the simplegmail library
    elif isinstance(messages, message.Message):
        message_dict = messages.__dict__
        messages = Constent.filter_fields(message_dict, labels_to_list)

    return messages

def fetch_message_and_message_labels(message_id, labels) -> dict:
    """
    Fetches a single message from the database and its labels.
    """
    db = shared_resources.client["Deft"]
    label_names = shared_resources.get_labels(labels, 0)
    message_collection = db["Messages"]
    message = message_collection.find_one({"id": message_id})
    return message, label_names


def update_messages_after_action(message, message_id):
    message_collection = db["Messages"]
    message_collection.delete_one({"id": message['id']})
    message = data_base.purify_message(message)
    message_collection.insert_one(message)
    db["Users"].update_one({"email": session['email']}, {"$pull": {"unread": message_id}})
    
def find_user(email):
    db = shared_resources.client["Deft"]
    user = db["Users"].count_documents({"email": email})
    return user

def pull_id_from_users_by_label(email, label, message_id):
    db = shared_resources.client["Deft"]
    db["Users"].update_one({"email": email}, {"$pull": {label: message_id}})
    
def insert_id_to_Users_by_label(email, label, message_id):
    db = shared_resources.client["Deft"]
    db["Users"].update_one({"email": email}, {"$push": {label: message_id}})
    
def delete_from_collection(collection_name, message_id):
    db = shared_resources.client["Deft"]
    db[collection_name].delete_one({"id": message_id})

def insert_one_document_to_collection(collection_name, message):
    db = shared_resources.client["Deft"]
    message = purify_message(message)
    db[collection_name].insert_one(message)
    
def insert_many_documents_to_collection(collection_name, messages):
    db = shared_resources.client["Deft"]
    messages = purify_message(messages)
    db[collection_name].insert_many(messages)