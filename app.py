import logging
import sys
from datetime import date
import os
import webbrowser
from threading import Timer
import pymongo
import data_base
import shared_resources
from constent import Constent
from flask import (Flask, flash, jsonify, redirect, render_template, request, session, url_for)
from simplegmail import Gmail
from simplegmail.query import construct_query
from googleapiclient.discovery import build
from oauth2client.client import AccessTokenCredentials, HttpAccessTokenRefreshError


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
        db = shared_resources.client["Deft"]
        user_email = request.form['email']
        session['email'] = user_email
        found = db["Users"].count_documents({"email": user_email})
        if not found:
            logging.info("making a new document for the user...")
            data_base.make_db(user_email) 
            data_base.init_db(user_email)
        else:
            data_base.update_db(user_email)
        try:
            #try to envoke the credentials
            gmail.get_drafts()
        except HttpAccessTokenRefreshError as e:
                if "Token has been expired or revoked" in str(e):
                    logging.error("Token has been expired or revoked. Refreshing token...")
                    credentials = OAuth2Credentials.from_json(session['credentials'])
                    if credentials.access_token_expired:
                        credentials.refresh(httplib2.Http())
                        session['credentials'] = credentials.to_json()
                
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
    if not str_date and not end_date:
        str_date = request.form.get('start-date')
        end_date = request.form.get('end-date')
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
    #TODO: a db version of get all the messages by sender
    return render_template("user.html", messages=messages, labels=gmail.list_labels(), get_name=shared_resources.get_email_sender_name, title="By Source")


@app.route('/api/v1/gmail/messages/by_label/<string:wanted_label>', methods=["POST",'GET'])
def get_messages_by_label(wanted_label):
    data = {    
        "label": wanted_label
    }
    db = shared_resources.client["Deft"]
    message_collection = db["Messages"]
        
    user_document = db["Users"].find_one({"email": session['email'].strip()})
    wanted_label_messages_ids = user_document.get(wanted_label, [])
    wanted_label_messages_ids = list(set(wanted_label_messages_ids))
    messages = list( db["Messages"].find({"id": {"$in": wanted_label_messages_ids}}))    
    #drops the initial "category_"
    if wanted_label[:9] == "CATEGORY_":
        wanted_label = wanted_label[9:].lower().capitalize()
    
    return render_template("user.html", messages=messages, labels=gmail.list_labels(), get_name=shared_resources.get_email_sender_name, title=wanted_label)


@app.route('/api/v1/gmail/messages/show_message_info/<message_id>/<labels>', methods=['GET'])
def show_message_info(message_id,labels):
    found = False
    message_from_gmail = None
    db = shared_resources.client["Deft"]
    label_names = shared_resources.get_labels(labels, 0)
    message_collection = db["Messages"]
    message = message_collection.find_one({"id": message_id}) 
    if message:
        found = True
    message_from_gmail = shared_resources.get_message_by_id(message_id) #TODO: make it in async??
    if "UNREAD" in label_names:
        if message_from_gmail is not None: # message_from_gmail is None if the message is in the trash
            message_from_gmail.mark_as_read()  
        #update db
        if found:    
            message_collection = db["Messages"]
            message_collection.delete_one({"id": message['id']})
            message = data_base.purify_message(message)
            message_collection.insert_one(message)
            db["Users"].update_one({"email": session['email']}, {"$pull": {"unread": message_id}})
        elif message_from_gmail is not None:
            return render_template("message_info.html",title="message info" , message=message_from_gmail)

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
    email = session['email']
    db = shared_resources.client["Deft"]
    
    message_id = request.form.get('message_id')
    if message_id is None:
        message_id = session.get('message_id')
        
    msg = shared_resources.get_message_by_id(message_id)
    if msg is None: 
        """
        If msg is None it means that the user want to delete a message that is already in the trash
        Hance we need to delete it from the db and the gmail account.
        """
        db["Users"].update_one({"email": session['email']}, {"$pull": {"TRASH": message_id}})
        db["Messages"].delete_one({"id": message_id}) 

        return redirect(url_for("get_messages_by_label", wanted_label="TRASH"))

    for label in msg.label_ids:
      db["Users"].update_one({"email": email}, {"$pull": {label.name: msg.id}})  
        
    db["Users"].update_one({"email": email}, {"$push": {"TRASH": message_id}}) 
    db["Messages"].delete_one({"id": msg.id})
    db["Messages"].insert_one(data_base.purify_message(msg))
    msg.trash()

    return redirect(url_for("get_brief_of_today"))


@app.route('/api/v1/gmail/messages/add_label_to_message', methods=['POST'])
def add_label_to_message():
        desired_message_id = request.form['message_id']
        desired_label = request.form['wanted_label'] #TODO: hebrew letters are invalid
        msg = shared_resources.get_message_by_id(desired_message_id)
        
        email = session['email']
        db = shared_resources.client["Deft"]   
        
        if desired_label == "TRASH":
            if msg:
                msg.mark_as_not_important()
                msg.mark_as_read()
                
            session['message_id'] = desired_message_id
            return redirect(url_for("move_to_garbage"))
        elif desired_label == "SPAM":
            if msg:
                msg.mark_as_spam()
                msg.mark_as_not_important()
                msg.mark_as_read()
                
            Constent.move_to_the_right_label(email,"SPAM",desired_message_id,db)
        else:
            if msg:
                msg.add_label(desired_label)
                
            Constent.move_to_the_right_label(email,desired_label,desired_message_id,db)
    
        return redirect(url_for("get_brief_of_today"))


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            Timer(1, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    app.run(debug=True)