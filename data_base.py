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
from simplegmail import Gmail
from simplegmail.query import construct_query
import logging

logging.basicConfig(level=logging.INFO)
gmail = Gmail()


categories = ["CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS", "CATEGORY_PERSONAL", "CATEGORY_PRIMARY"]



def init_db(email) -> None:


    db = shared_resources.client[shared_resources.get_name_from_email(email)]


    collections = db.list_collection_names()

    for coll in collections:
        

        messages = gmail.get_messages(query=f"label: {coll}")


        messages = purify_message(messages)
        
        
        db[coll].insert_many(messages)



def make_db(email) -> None:
    """

    makes a database for the user with the email as the name & creates a collection for each label 
    """
    db = shared_resources.client[shared_resources.get_name_from_email(email)]

    labels = gmail.list_labels()

    for label in labels:
        db.create_collection(label.name)
    
    
    db.create_collection("Filter")
    filter_collection = db["Filter"]
   # make a dict of the labels that contian a list as valuse
    filter_labels = {label.name: [] for label in labels}
    filter_collection.insert_one(filter_labels)


def update_db(email) -> None:
    """

    Get the messages from the user gmail account and check if there's a message that dosent exist in the collection

    by checking the id & recipient of the message
    """
    shadow_categories = {category: {} for category in categories}
    
    db = shared_resources.client[shared_resources.get_name_from_email(email)]
    collections = db.list_collection_names() 
        
    for i in range(len(collections)): 
        data = { "label" : collections[i]}
        messages = gmail.get_messages(query=construct_query(**data))


        for j in range(len(messages)):  
            
            # get the labels of the message
            labels_of_message = messages[j].label_ids
            labels_of_message = shared_resources.get_labels(labels_of_message, 1)
            
            for t in range(len(labels_of_message)):
                
               if labels_of_message[t] in categories:
                   # add the message to the shadow category
                     shadow_categories[labels_of_message[t]][messages[j].id] = messages[j]
               
            if db[collections[i]].find_one({"id": messages[j].id, "recipient": messages[j].recipient}) is None:
                logging.info(f"message --- {messages[j].id} not in {collections[i]} ==================================================")
                # clean the collection to avoid duplicates
                db[collections[i]].delete_many({})
                db[collections[i]].insert_many(purify_message(messages))
            
        
    # update the shadow categories
    for category in categories:
        if list(shadow_categories[category].values()) != []:
            db[category].delete_many({})
            logging.info(f"SHADOW inserted message in category --- {category} ======================")
            db[category].insert_many(purify_message(list(shadow_categories[category].values())))



def labels_to_list(labels)-> list[list[str]]:
    return [[label.name, label.id] for label in labels]



def add_filter_collection(name, label):
    db = shared_resources.client[shared_resources.get_name_from_email(email)]
    filter_collection = db["Filter"]
    
    
    


def purify_message(messages) -> list[dict]:
    """
    makes the messages list to be valid for mongoDB
    """
    fields = Constent.fields
    logging.info(f"fields: {fields}")
   
    if isinstance(messages, list):
        messages = [message.__dict__ for message in messages]  
        messages = [Constent.filter_fields(message, labels_to_list) for message in messages]  
   # if the messages is a single message, message is an object from the simplegmail library
    elif isinstance(messages, simplegmail.message.Message):
        message_dict = messages.__dict__
        messages = Constent.filter_fields(message_dict, labels_to_list)

    return messages