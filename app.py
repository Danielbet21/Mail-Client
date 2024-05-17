import logging
import sys
from datetime import date
import os
import webbrowser
from threading import Timer

import pymongo

import data_base
import shared_resources

from flask import (Flask, flash, jsonify, redirect, render_template, request, session, url_for)

from simplegmail import Gmail
from simplegmail.query import construct_query


app = Flask(__name__)
app.secret_key = "secret"
sys.stdout.reconfigure(encoding='utf-8')

gmail = Gmail()

logging.basicConfig(level=logging.INFO)

                                                          
@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/api/v1/gmail/login", methods=["POST", "GET"])
def login():
    if request.method == 'POST':


        full_email = request.form['email']
    
        db_name = shared_resources.get_name_from_email(full_email)


        session['email'] = db_name
        data_base.update_db(session['email'])


        if db_name not in shared_resources.client.list_database_names():
            data_base.init_db(db_name)
            data_base.make_db(db_name)  

        #TODO: make an error handling for:
        # oauth2client.client.HttpAccessTokenRefreshError: invalid_grant: Token has been expired or revoked.
        return redirect(url_for("get_brief_of_today"))

    return render_template("login.html")


@app.route("/api/v1/gmail/user/", methods=["POST", "GET"])
def user():
    data_base.update_db(session['email'])
    
    messages = shared_resources.get_messages_inbox()
    messages = data_base.purify_message(messages)

    return render_template("user.html", messages=messages, labels=gmail.list_labels(), get_name=shared_resources.get_email_sender_name, title="Inbox")


@app.route('/api/v1/gmail/messages/brief_of_today', methods=['GET'])
def get_brief_of_today():
        today = date.today()
        param = {
            "after": today
        }

        messages = gmail.get_messages(query=construct_query(**param))
        if len(messages) == 0:
            flash("No messages for today...")
            return redirect(url_for("user"))
        
        messages = data_base.purify_message(messages)

        return render_template("user.html", messages=messages, title="Today's Brief", labels=gmail.list_labels(), get_name=shared_resources.get_email_sender_name)


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

    return render_template("user.html", messages=messages, title="Message By Date", labels=gmail.list_labels(), get_name=shared_resources.get_email_sender_name)


@app.route('/api/v1/gmail/messages/<sender_email>', methods=['GET'])
def get_messages_by_source(sender_email: str):
    messages = gmail.get_messages(query=f"from: {sender_email}")
    #TODO: make a db version
    return render_template("user.html", messages=messages, labels=gmail.list_labels(), get_name=shared_resources.get_email_sender_name, title="By Source")


@app.route('/api/v1/gmail/messages/by_label/<string:wanted_label>', methods=["POST",'GET'])
def get_messages_by_label(wanted_label):

    data = {    
        "label": wanted_label
    }
    db = shared_resources.client[session['email']]
    collection = db[wanted_label]
    messages = collection.find()
    
    #drops the initial "category_"
    if wanted_label[:9] == "CATEGORY_":
        wanted_label = wanted_label[9:].lower().capitalize()
    
    return render_template("user.html", messages=messages, labels=gmail.list_labels(), get_name=shared_resources.get_email_sender_name, title=wanted_label)


@app.route('/api/v1/gmail/messages/show_message_info/<message_id>/<labels>', methods=['GET'])
def show_message_info(message_id,labels):
    found = False
    message1 = None
        
    db = shared_resources.client[session['email']]    
    label_names = shared_resources.get_labels(labels, 0)
    
    # search for the message in the db
    for label in label_names:
        collection = db[label]
        message = collection.find_one({"id": message_id}) 
        if message:
            found = True
            break
        
    # update the gmail webpage
    message1 = shared_resources.get_message_by_id(message_id) #TODO: make it in async??
    
    if "UNREAD" in label_names:
        message1.mark_as_read()
        #update db
        if found:    
            target_collection = db["UNREAD"]
            target_collection.delete_one({"id": message['id']}) 
            
    return render_template("message_info.html",title="message info" , message=message)


@app.post('/api/v1/gmail/messages/send')
def send_message():

    if request.method == 'POST':
        email = session['email']
        full_address = email + "@gmail.com"
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

        return redirect(url_for("get_brief_of_today"))


@app.get('/api/v1/gmail/messages/send')
def display_send_massage_page():

    return render_template("send_msg.html")


@app.route('/api/v1/gmail/messages/move_to_garbage', methods=['POST', 'GET'])
def move_to_garbage():
    message_id = request.form.get('message_id')

    if message_id is None:
        message_id = session.get('message_id')
    
    msg = shared_resources.get_message_by_id(message_id)
    
    
    # update the db
    email = session['email']
    db = shared_resources.client[shared_resources.get_name_from_email(email)]

    for label in msg.label_ids:

        target_collection = db[label.name]

        target_collection.delete_one({"id": msg.id})
        
    db["TRASH"].insert_one(data_base.purify_message(msg))
    
    # every msg must be read in order to go into the trash
    msg.mark_as_read()
    msg.trash()
    
    return redirect(url_for("get_brief_of_today"))


@app.route('/api/v1/gmail/messages/add_label_to_message', methods=['POST'])
def add_label_to_message():


        desired_message_id = request.form['message_id']
        desired_label = request.form['wanted_label'] #TODO: hebrew letters are invalid
        
        msg = shared_resources.get_message_by_id(desired_message_id)


        if desired_label == "TRASH":

            msg.mark_as_not_important()

            msg.mark_as_read()

            session['message_id'] = desired_message_id

            return redirect(url_for("move_to_garbage"))


        msg.add_label(desired_label)
        

        # update the db
        email = session['email']
        db = shared_resources.client[shared_resources.get_name_from_email(email)]    

        anti_inbox = gmail.list_labels()
        anti_inbox.remove("INBOX")
        
        if desired_label in anti_inbox:
            target_collection = db["INBOX"]
            target_collection.delete_one({"id": the_msg.id}) 
        
        target_collection = db[desired_label]
        target_collection.insert_one(data_base.purify_message(the_msg))
        
        return redirect(url_for("get_brief_of_today"))


if __name__ == "__main__":

    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            Timer(1, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    
    app.run(debug=True)