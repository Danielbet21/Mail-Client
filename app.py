import json
import logging

import sys
from datetime import date

import pymongo
from email.utils import parseaddr
from flask import (Flask, flash, jsonify, redirect, render_template, request, session, url_for)
from simplegmail import Gmail
from simplegmail.query import construct_query



app = Flask(__name__)
app.secret_key = "secret"

sys.stdout.reconfigure(encoding='utf-8')

gmail = Gmail()

logging.basicConfig(level=logging.INFO)

client = pymongo.MongoClient("mongodb://localhost:27017/")


#--------------------------------------------------------------------------------------------------------------------------------------
#                                                            Functions

def get_message_by_id(desired_message_id: str):

    messages = gmail.get_messages()

    for message in messages:

        if message.id == desired_message_id:

            the_msg = message

            break

    return the_msg



def get_email_sender_name(message: str) -> str:
    
    return parseaddr(message)[0]




def get_name_from_email(email) -> str:

    return str(email.split('@')[0])


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


def make_db(email) -> None:
    """
    makes a database for the user with the email as the name & creates a collection for each label
    for fast access to the messages 
    """
    db = client[get_name_from_email(email)]

    labels = gmail.list_labels()


    for label in labels:
        temp = db.create_collection(label.name)



def init_db(email) -> None:


    db = client[get_name_from_email(email)]


    collections = db.list_collection_names()


    for coll in collections:


        messages = gmail.get_messages(query=f"label: {coll}")

        messages = purify_message(messages)

        db[coll].insert_many(messages)


def update_db(email) -> None:
    """
    Get the messages from the user gmail account and check if there's a message that dosent exist in the collection
    by checking the id & recipient of the message
    """
    db = client[get_name_from_email(email)] 

    collections = db.list_collection_names() 

    for i in range(len(collections)): 
        data = { "label" : collections[i]}
        messages = gmail.get_messages(query=construct_query(**data))
        
        for j in range(len(messages)):
            if db[collections[i]].find_one({"id": messages[j].id, "recipient": messages[j].recipient}) is None:
                db[collections[i]].insert_many(purify_message(messages))
    
    
def get_messages_inbox():
        params = {

            "labels": "INBOX"

        }
        messages = gmail.get_messages(query=construct_query(params))
        return messages
    
#--------------------------------------------------------------------------------------------------------------------------------------
#                                                            Routes


@app.route("/")
def home():
    return redirect(url_for("get_brief_of_today"))




@app.route("/api/v1/gmail/login", methods=["POST", "GET"])
def login():

    if request.method == 'POST':

        email = request.form['email']
    
        db_name = get_name_from_email(email)

        session['email'] = db_name
        
        if db_name not in client.list_database_names():
            make_db(email)  
        
        db_list = client.list_database_names()
        if db_name not in db_list:
            init_db(email)

        update_db(email)
        return redirect(url_for("get_brief_of_today"))


    return render_template("login.html")
    
    


@app.route("/api/v1/gmail/logout")
def logout():
    pass



@app.route("/api/v1/gmail/user/")
def user():

    messages = get_messages_inbox()

    return render_template("user.html", messages=messages, labels=gmail.list_labels(), get_name=get_email_sender_name, title="Inbox")



@app.route('/api/v1/gmail/messages/brief_of_today', methods=['GET'])
def get_brief_of_today():
        today = date.today()

        param = {

            "after": today

        }

        messages = gmail.get_messages(query=construct_query(**param))

        if len(messages) == 0:
            flash("No messages for today...  Moving to your Inbox")
            return redirect(url_for("user"))

        return render_template("user.html", messages=messages, title="Today's Brief", labels=gmail.list_labels(), get_name=get_email_sender_name)



@app.route('/api/v1/gmail/messages/<string:str_date>/<string:end_date>', methods=['GET'])
def get_messages_by_date(str_date: str, end_date: str):
    """
    - end_date and str_date should be in the format of "YYYY-MM-DD"


    - end_date is not included in the search


    Currently, the emails includes all the the messages sent and resicved by & from the user
    """

    dates = {

        "after": str_date,

        "before": end_date

    }

    logging.info(f'fetching messages from date: {str_date} up until {end_date}')

    messages = gmail.get_messages(query=construct_query(**dates))

    return render_template("user.html", messages=messages, title="Message By Date", labels=gmail.list_labels(), get_name=get_email_sender_name)





@app.route('/api/v1/gmail/messages/<string:sender_email>', methods=['GET'])


def get_messages_by_source(sender_email: str):


    try:

        messages = gmail.get_messages(query=f"from: {sender_email}")
        return redirect(url_for("user"))


    except Exception as e:
        return jsonify({'get_messages_by_source | error': str(e)}), 500




@app.route('/api/v1/gmail/messages/unread', methods=['GET'])
def get_unread_messages():
    
    messages = gmail.get_unread_inbox()
    return render_template("user.html", messages=messages, labels=gmail.list_labels(), get_name=get_email_sender_name, title="Inbox")




@app.route('/api/v1/gmail/messages/by_label/<string:wanted_label>', methods=["POST",'GET'])
def get_messages_by_label(wanted_label):
    data = {    
        "label": wanted_label
    }
    messages = gmail.get_messages(query=construct_query(**data ))
    return render_template("user.html", messages=messages, labels=gmail.list_labels(), get_name=get_email_sender_name, title=wanted_label)




@app.route('/api/v1/gmail/messages/send', methods=['POST', 'GET'])


def send_message():


    if request.method == 'POST':
        
        email = session['email']
        full_address = email + "@gmail.com"

        try:
            to = request.form['to']
            subject = request.form['subject']
            message = request.form['message']

            if not to or not message:
                return redirect(url_for("send_message"))

            data = {
                "to": to,

                "sender": full_address,

                "subject": subject,

                "msg_html": message,

                "msg_plain": message,

                "signature": True
            }


            sent = gmail.send_message(**data)
            return redirect(url_for("user"))

        except Exception as e: #TODO: do i need it?
            return jsonify({'send_message | error': str(e)}), 500
        

    elif request.method == 'GET':
        return render_template("send_msg.html")

    else:
        raise Exception(f'method: {request.method} is not implemented')




@app.route('/api/v1/gmail/messages/move_to_garbage', methods=['POST'])

def move_to_garbage():

    message_id = request.form.get('message_id')

    try:
        if message_id:
            the_msg = get_message_by_id(message_id)

        else:
            pass

        # update the db

        email = session['email']

        db = client[get_name_from_email(email)]


        for label in the_msg.label_ids:
            target_collection = db[label.name]
            target_collection.delete_one({"id": the_msg.id})
            

        trash_collection = db["TRASH"]
        trash_collection.insert_one(purify_message(the_msg))
        
        # every msg must be read in order to go into the trash
        the_msg.mark_as_read()
        the_msg.trash()
        
        return redirect(url_for("get_brief_of_today"))


    except Exception as e:
        return jsonify({'move_to_garbage | error': str(e)}), 500




@app.route('/api/v1/gmail/messages/add_label', methods=['POST'])

def add_label():


    try:


        desired_message_id = request.form['message_id']

        desired_label = request.form['wanted_label']


        the_msg = get_message_by_id(desired_message_id)


        if desired_label == "TRASH":

            return redirect(url_for("move_to_garbage"))


        the_msg.add_label(desired_label)
        return redirect(url_for("user"))


    except Exception as e:

        return jsonify({'add_label | error': str(e)}), 500




if __name__ == "__main__":


    app.run(debug=True)