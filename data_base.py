"""
data_base.py: The Data Access Layer (DAL) of the project.
This library interacts with the MongoDB , SQLite databases and the Gmail API to fetch, process, and store email data.
It provides functions to initialize, update, and manage the database and more.
"""
from constent import *
import base64
import shared_resources
import pymongo
from simplegmail import Gmail , message , label, attachment
from simplegmail.query import construct_query
import logging
import sqlite_file
from datetime import datetime, timezone
from dateutil import parser
logging.basicConfig(level=logging.INFO)
gmail = Gmail()

categories = {"CATEGORY_SOCIAL": "CATEGORY_SOCIAL","CATEGORY_PROMOTIONS": "CATEGORY_PROMOTIONS","CATEGORY_UPDATES": "CATEGORY_UPDATES","CATEGORY_FORUMS": "CATEGORY_FORUMS","CATEGORY_PERSONAL": "CATEGORY_PERSONAL","CATEGORY_PRIMARY": "CATEGORY_PRIMARY"}



def init_db(email) -> None:
    """
    Init the database with the user email data for the first time
    """
    db = shared_resources.client["Deft"]
    users_collection = db["Users"]
    message_collection = db["Messages"]
    labels = gmail.list_labels()
    
    for label in labels:
        messages = gmail.get_messages(query=f"label:{label.name}")
        if messages:
            latest_message_date = convert_date_to_utc(messages[0].date)
            label_message_ids = [] 
            
            for msg in messages:
                msg.date = convert_date_to_utc(msg.date)
                if message_collection.count_documents({"id": msg.id}) == 0:
                    purified_message = purify_message(msg)
                    message_collection.insert_one(purified_message)
                else:
                    purified_message = purify_message(msg)
                    
                label_message_ids.append(purified_message["id"])
                
            users_collection.update_one({"email": email}, {"$push": {label.name: {"$each": label_message_ids}}})
            update_and_check_latest_message(email, latest_message_date)
           
            for message in messages: 
                labels = {label.name: label.name for label in message.label_ids}

                if "TRASH" not in labels:
                    for label_element in labels:
                        label_element = label.name if hasattr(label, 'name') else label_element
                        if categories.get(label_element):
                            category_handler(message, label_element, email)


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
        users_collection.insert_one({"email": email, "name": email_name_of_user, **label_lists, "latest_message": datetime(1970, 1, 1, tzinfo=timezone.utc)})


def update_db(email) -> None:
    """
    Get the messages from the user gmail account and check if there's a message that dosent exist in the collection
    by checking the id & labels of the message
    """
    db = shared_resources.client["Deft"]
    users_collection = db["Users"]
    message_collection = db["Messages"]

    current_latest_message_dict = users_collection.find_one({"email": email}, {"latest_message": 1})
    current_latest_message = current_latest_message_dict.get("latest_message")
    current_latest_message = current_latest_message.replace(tzinfo=timezone.utc)
    latest_message_date = None
    labels = gmail.list_labels()
    
    if Constent.there_is_messages_after_latest_message_from_gmail(gmail, users_collection, current_latest_message):
        for label in labels:
            messages = gmail.get_messages(query=f"label: {label.name}")
            if messages:
                latest_message_date = convert_date_to_utc(messages[0].date)
                has_newer = update_and_check_latest_message(email, latest_message_date)
                if has_newer:
                    for msg in messages:   
                        found =  message_collection.count_documents({"id": msg.id, "label_ids": labels_to_list(msg.label_ids)})
                        if not found:
                            found_with_other_labels = message_collection.find_one({"id": msg.id})
                            if found_with_other_labels:
                                message_collection.delete_one({"id": msg.id})   
                            
                            msg = purify_message(msg)
                            msg["date"] = convert_date_to_utc(msg["date"])
                            message_collection.insert_one(msg)
                            
                            if (not found_with_other_labels) and( "TRASH" not in msg["label_ids"]):
                                x = msg["subject"]
                                for label in msg["label_ids"]:
                                    if categories.get(label):
                                        category_handler(msg, label, email)
    else:
        logging.info("\n\n update_db: Nothing happaned here \n ==================== \n")

def category_handler(message, label, email)-> None:
    db = shared_resources.client["Deft"]
    user_collection = db["Users"]
    message = purify_message(message)
    user_collection.update_one({"email": email}, {"$push": {label: message["id"]}})


def update_and_check_latest_message(email, latest_message_date)-> bool:
    db = shared_resources.client["Deft"]
    user_collection = db["Users"]
    
    latest_dict = user_collection.find_one({"email": email}, {"latest_message": 1})
    current_latest_date = latest_dict.get("latest_message")
    if current_latest_date:
        current_latest_date = current_latest_date.replace(tzinfo=timezone.utc)
        
    if current_latest_date and (current_latest_date < latest_message_date):
        user_collection.update_one({"email": email}, {"$set": {"latest_message": latest_message_date}})
        return True
    
    return False


def labels_to_list(labels)-> list[str]: #TODO: change the insertion to the function 
    if isinstance(labels[0], label.Label):
        return [label.name for label in labels]
    elif isinstance(labels, str):
        return [label for label in labels]


def purify_message(messages) -> list[dict]:
    """
    Makes the messages list to be valid for mongoDB
    """
    def process_message(message):
        message_dict = message.__dict__
        message_dict = Constent.filter_fields(message_dict, labels_to_list)
        message_dict['date'] = convert_date_to_utc(message_dict['date'])
        return message_dict

    if isinstance(messages, list):
        messages = [process_message(message) for message in messages]
    elif isinstance(messages, message.Message):
        messages = process_message(messages)

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


def update_messages_after_action(message, message_id)-> None:
    db = shared_resources.client["Deft"]
    message_collection = db["Messages"]
    
    message_collection.delete_one({"id": message['id']})
    message = purify_message(message)
    message_collection.insert_one(message)
    db["Users"].update_one({"email": session['email']}, {"$pull": {"unread": message_id}})


def make_as_read(email,desired_label,desired_message_id,db) -> None:
        db["Users"].update_one({"email":email}, {"$pull": {"UNREAD": desired_message_id}})
        db["Users"].update_one({"email":email}, {"$push": {desired_label: desired_message_id}})
        

def find_user(email)-> int:
    db = shared_resources.client["Deft"]
    user_count = db["Users"].count_documents({"email": email})
    return user_count


def pull_id_from_users_by_label(email, label, message_id)-> None:
    db = shared_resources.client["Deft"]
    db["Users"].update_one({"email": email}, {"$pull": {label: message_id}})
    
    
def insert_id_to_Users_by_label(email, label, message_id)-> None:
    db = shared_resources.client["Deft"]
    db["Users"].update_one({"email": email}, {"$push": {label: message_id}})
    
    
def delete_from_collection(collection_name, message_id)-> None:
    db = shared_resources.client["Deft"]
    db[collection_name].delete_one({"id": message_id})


def insert_one_document_to_collection(collection_name, message)-> None:
    db = shared_resources.client["Deft"]
    message = purify_message(message)
    db[collection_name].insert_one(message)
    
    
def insert_many_documents_to_collection(collection_name, messages)-> None:
    db = shared_resources.client["Deft"]
    messages = purify_message(messages)
    db[collection_name].insert_many(messages)
    

def get_all_ids_for_user(email)-> list:
    db = shared_resources.client["Deft"]
    user = db["Users"].find_one({"email": email})

    return user["all_ids"]


def convert_date_to_utc(date_input)-> datetime:
    if isinstance(date_input, datetime):
        return date_input
    else:
        date = parser.isoparse(date_input)    
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        else:
            date = date.astimezone(timezone.utc)    
        return date

def get_all_messages_erlier_than_latest_message(message_collection) -> list:
        todays_date = Constent.get_today_date()
        messages  = message_collection.find({"date":{"$gte": todays_date}, "label_ids":{"$ne": "TRASH"}}).sort("date", -1)   
        messages = list(messages)
        messages = remove_duplicates_from_list(messages)
        return messages
    
def remove_duplicates_from_list(messages)-> list:
    seen = list()
    unique_messages = []
    for message in messages:
        if message["id"] not in seen:
            seen.append(message["id"])
            unique_messages.append(message)
    
    return unique_messages

def insert_label_to_message(email, label, message_id, db) -> None:
    db["Messages"].update_one({"email": email, "id": message_id},{"$push": {"label_ids": label}})
    logging.info(f"\n\ninsert_label_to_message: {label} was added to message {message_id} for user {email} ==================== \n\n")