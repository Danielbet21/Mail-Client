import logging
import threading
import sys
from datetime import date, datetime, timedelta
from dateutil import parser
import os
import webbrowser
from threading import Timer
from flask import (Flask, flash, jsonify, redirect, render_template, request, session, url_for, send_file)
from apscheduler.schedulers.background import BackgroundScheduler
from apschedular import SchedulerManager  
from apscheduler.triggers.interval import IntervalTrigger
from simplegmail import Gmail
from simplegmail.query import construct_query
from oauth2client.client import HttpAccessTokenRefreshError
from dotenv import load_dotenv
from openai import OpenAI
import pymongo
import data_base
import shared_resources
import sqlite_file 
from constent import Constent

# Load environment variables
load_dotenv()

sqlite_file.init_sqlite()

app = Flask(__name__)
app.secret_key = "secret"

logging.basicConfig(level=logging.INFO)
sys.stdout.reconfigure(encoding='utf-8')

gmail = Gmail()

# Initialize APScheduler
scheduler = BackgroundScheduler()

                          
@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/api/v1/gmail/login", methods=["POST", "GET"])
def login(): #TODO: make sure this solve the problem of the token
    if request.method == 'POST':
        user_email = request.form['email']
        session['email'] = user_email
        SchedulerManager.start_scheduler(scheduler, gmail, session['email'])
        found = data_base.find_user(session['email'])
        if not found:
            data_base.make_db(user_email) 
            data_base.init_db(user_email)
        else:
            data_base.update_db(user_email)
            
        try:
            gmail.list_labels()
        except HttpAccessTokenRefreshError as e:
            return Constent.handle_token_error(e)

        return redirect(url_for("get_brief_of_today"))
    return render_template("login.html")


@app.route("/api/v1/gmail/user/", methods=["POST", "GET"])
def user(is_done = False):
    if not is_done:
        data_base.update_db(session['email'])

    messages = shared_resources.get_messages_inbox()
    messages = data_base.purify_message(messages)
    return render_template("user.html", messages=messages, labels=gmail.list_labels(), get_name=shared_resources.get_email_sender_name, title="Inbox")


@app.route('/api/v1/gmail/messages/brief_of_today', methods=['GET'])
def get_brief_of_today():
        db = shared_resources.client["Deft"]
        users_collection = db["Users"]
        message_collection = db["Messages"]
        
        messages = Constent.get_all_messages_erlier_than_latest_message(message_collection)
        logging.info(f"\n\nFound {len(messages)} messages for today\n")
        if not messages:
            return redirect(url_for("user", is_done=True))
        return render_template("user.html", messages=messages, title="Today's Brief", labels=gmail.list_labels(), get_name=shared_resources.get_email_sender_name)


@app.route('/api/v1/gmail/messages/<string:str_date>/<string:end_date>', methods=['GET'])
def get_messages_by_date(str_date: str, end_date: str):
    """
    - end_date and str_date should be in the format of "YYYY-MM-DD"
    - end_date is not included in the search
    Currently, the emails includes all the the messages sent and resicved by & from the user
    """
    # if not str_date and not end_date:
    #     str_date = request.form.get('start-date')
    #     end_date = request.form.get('end-date')
    dates = {
        "after": str_date,
        "before": end_date
    }
    messages = gmail.get_messages(query=construct_query(**dates)) #TODO: make a db version of get all the messages by date
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
def show_message_info(message_id, labels):
    attachments = []
    message, label_names = data_base.fetch_message_and_message_labels(message_id, labels)
    #TODO: fetch attachments from the sqlite db
    subject = message['subject']
    date = message['date']
    if "UNREAD" in label_names:
        thread = threading.Thread(target=Constent.mark_gmail_message_as_read, args=(message_id,date,subject))
        thread.start()
    else:
        attachments = sqlite_file.get_attachments_by_message_id(message_id)
        
    if attachments is None:
        message = shared_resources.get_message_by_id_from_gmail(message_id,date,subject)
        attachments = sqlite_file.get_attachments_by_message_id(message_id)
    
    return render_template("message_info.html", title="message info", message=message, attachments=attachments , labels=gmail.list_labels())



@app.post('/api/v1/gmail/messages/send')
def send_message():
    email = session['email']
    full_address = email
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

    return redirect(url_for("get_brief_of_today", labels=gmail.list_labels()))


@app.get('/api/v1/gmail/messages/send')
def display_send_massage_page():
    
    return render_template("send_msg.html", labels=gmail.list_labels())


@app.route('/api/v1/chat', methods=['POST'])
def chat():
    # Initialize the OpenAI client with the API key
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    user_message = request.json.get('message')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Help the user to write an email based on their request. Answer shortly and clearly."},
            {"role": "user", "content": user_message}
        ],
        max_tokens=150
    )
    
    bot_response = chat_completion.choices[0].message.content.strip()
    return jsonify({'response': bot_response})



@app.route('/api/v1/gmail/messages/move_to_garbage', methods=['POST', 'GET'])
def move_to_garbage():
    email = session['email']
    db = shared_resources.client["Deft"]
    
    message_id = request.form.get('message_id')
    if message_id is None:
        message_id = session.get('message_id')
        
    message, labels = data_base.fetch_message_and_message_labels(message_id, None)
    msg = shared_resources.get_message_by_id_from_gmail(message_id,message['date'],message['subject'])
    if msg is None: 
        """
        the user want to delete a message that is already in the trash=>need to delete it from the db and the gmail account.
        #TODO: delete the message from gmail permenatly
        """
        data_base.pull_id_from_users_by_label(email, "TRASH", message_id)
        data_base.delete_from_collection("Messages", message_id)
        return redirect(url_for("get_messages_by_label", wanted_label="TRASH"))

    for label in msg.label_ids:
      data_base.pull_id_from_users_by_label(email, label.name, msg.id)
        
    data_base.insert_id_to_Users_by_label(email, "TRASH", msg.id)
    data_base.delete_from_collection("Messages", msg.id)
    data_base.insert_one_document_to_collection("Messages", msg)
    msg.trash()

    return redirect(url_for("get_brief_of_today"))


@app.route('/api/v1/gmail/messages/add_label_to_message', methods=['POST'])
def add_label_to_message():
        desired_message_id = request.form['message_id']
        date = request.form['date']
        subject = request.form['subject']
        desired_label = request.form['wanted_label'] #TODO: hebrew letters are invalid
        msg = shared_resources.get_message_by_id_from_gmail(desired_message_id,date,subject) 
        
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


@app.route('/api/v1/gmail/messages/cached', methods=['GET'])
def get_cached_messages():
    db = shared_resources.client["Deft"]
    messages_collection = db["Messages"]
    timestamp = request.args.get('timestamp')
    if not timestamp:
        return jsonify({'error': 'Timestamp is required'}), 400

    try:
        current_time = parser.parse(timestamp)
    except ValueError:
        return jsonify({'error': 'Invalid timestamp format'}), 400

    five_minutes_ago = current_time - timedelta(minutes=5)

    messages = list(messages_collection.find({
        'date': {'$gte': five_minutes_ago}
    }))
    print(messages)

    return jsonify({'messages': messages})


@app.route('/api/v1/gmail/attachments/<message_id>/<filename>')
def download_attachment(message_id, filename):
    data = sqlite_file.get_attachment_data(message_id, filename)
    if data:
        return send_file(
            io.BytesIO(data),
            attachment_filename=filename,
            as_attachment=True
        )
    return abort(404, description="Attachment not found")

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            Timer(1, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    try:
        app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()