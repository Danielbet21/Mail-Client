"""
data_base.py: The Data Access Layer (DAL) of the project.

This module interacts with the MongoDB database and the Gmail API to fetch, process, and store email data. It provides functions to initialize, update, and manage the database.

Functions:
- init_db(email): Initializes the database with email data.
- make_db(email): Creates a new database for a user.
- update_db(email): Updates the database with new email data.
- purify_message(messages): Prepares email messages for database insertion.
"""

import shared_resources
import pymongo
from simplegmail import Gmail
from simplegmail.query import construct_query
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials
import logging

logging.basicConfig(level=logging.INFO)
gmail = Gmail()

# Gmail API setup
# creds = Credentials.from_authorized_user_file('gmail_token.json')
# service = build('gmail', 'v1', credentials=creds)
categories = ["CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS", "CATEGORY_PERSONAL", "CATEGORY_PRIMARY"]
# user_id = 'me'



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

        temp = db.create_collection(label.name)



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
                # clean the collection to avoid duplicates
                db[collections[i]].delete_many({})
                db[collections[i]].insert_many(purify_message(messages))
        
    # update the shadow categories
    for category in categories:
        if list(shadow_categories[category].values()) != []:
            db[category].delete_many({})
            db[category].insert_many(purify_message(list(shadow_categories[category].values())))

    
    
    
    
    
    
                

def purify_message(messages) -> list:
    """


    makes the messages list to be valid for mongoDB
    """


    fields = ["sender", 

              "subject", 

              "date", 

              "snippet",

              "user_id",

              "id",

              "thread_id",

              "recipient",

              "labels_id",

              "plain", 

              "html",

              "headers",
              
              "to", 

              "cc",

              "bcc"]  # TODO: add attachments field?
    

    if isinstance(messages, list):

        messages = [message.__dict__ for message in messages]  # convert messages to be a list of dictionaries

        messages = [{field: message.get(field, None) for field in fields} for message in messages]  # filter the fields

    else:

        # If it's a single message

        message_dict = messages.__dict__

        messages = {field: message_dict.get(field, None) for field in fields}

    return messages