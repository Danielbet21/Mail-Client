from datetime import date
import json
import logging
import sys
import pymongo

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from simplegmail.query import construct_query
from email.utils import parseaddr
from simplegmail import Gmail

app = Flask(__name__)
app.secret_key = "secret"
gmail = Gmail()
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)
client = pymongo.MongoClient("mongodb://localhost:27017/")


def get_labels():
    """
    get all the labels the current user have
    """
    return gmail.list_labels()


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/api/v1/gmail/login", methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        
        db_name = get_name_from_email(email)
        if db_name not in client.list_database_names():
            make_db(email)   # TODO: make this async
        init_db(email)
        return redirect(url_for("get_brief_of_today"))
    return render_template("login.html")


def make_db(email):
    """
    makes a database for the user with the email as the name & creates a collection for each label
    for fast access to the messages 
    """
    db = client[get_name_from_email(email)]
    labels = get_labels()
    for label in labels:
        temp = db.create_collection(label.name)


def init_db(email):
    db = client[get_name_from_email(email)]
    collections = db.list_collection_names()
    for coll in collections:
        messages = gmail.get_messages(query=f"label: {coll}")
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
                  "bcc"] #TODO: add attachments filed?
        if messages:
            messages = [message.__dict__ for message in messages] # convert to be valid for mongoDB
            messages = [{field: message.get(field, None) for field in fields} for message in messages] # filter the fields
            db[coll].insert_many(messages)
    
    
@app.route("/api/v1/gmail/logout")
def logout():
    pass


@app.route("/api/v1/gmail/user/")
def user():
    messages = get_messages_INBOX()
    return render_template("user.html", messages=messages, labels=get_labels(),
                           get_name=get_name_from_message, title="Inbox")


def get_name_from_message(message):
    """
    return's the name of the sender (jhon doe <jhondoe@gmail.com> ==> jhon doe)
    """
    return parseaddr(message)[0]

def get_name_from_email(email):
    return str(email.split('@')[0])


@app.route('/api/v1/gmail/messages', methods=['GET'])
def get_messages_INBOX():
    try:
        params = {
            "labels": "INBOX"
        }
        messages = gmail.get_messages(query=construct_query(params))
        return messages
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/brief_of_today', methods=['GET'])
def get_brief_of_today():
    try:
        today = date.today()
        param = {
            "after": today
        }
        messages = gmail.get_messages(query=construct_query(**param))
        if len(messages) == 0:
            flash("No messages for today...  Moving to your Inbox")
            return redirect(url_for("user"))
        return render_template("user.html", messages=messages, title="Today's Brief",
                               labels=get_labels(), get_name=get_name_from_message)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/<string:str_date>/<string:end_date>', methods=['GET'])
def get_messages_by_date(str_date, end_date):
    """
    - end_date and str_date should be in the format of "YYYY-MM-DD"
    - end_date is not included in the search
    Currently, the emails includes all the the messages sent and resicved by & from the user
    """
    try:
        dates = {
            "after": str_date,
            "before": end_date
        }
        logging.info(str_date)
        logging.info(end_date)

        messages = gmail.get_messages(query=construct_query(**dates))
        logging.info(messages)
        return render_template("user.html", messages=messages, title="Message By Date",
                               labels=get_labels(), get_name=get_name_from_message)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/<string:source>', methods=['GET'])
def get_messages_by_source(source):
    try:
        messages = gmail.get_messages(query=f"from: {source}")
        return redirect(url_for("user"))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/unread', methods=['GET'])
def get_unread_messages():
    try:
        messages = gmail.get_unread_inbox()
        return redirect(url_for("user"))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/<string:wanted_label>', methods=['GET'])
def get_messages_by_label(wanted_label):
    try:
        messages = gmail.get_messages(query=f"label: {wanted_label}")
        return redirect(url_for("user"))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/send', methods=['POST', 'GET'])
def send_message():
    if request.method == 'POST':
        try:
            to = request.form['to']
            subject = request.form['subject']
            message = request.form['message']
            if not to or not message:
                return redirect(url_for("send_message"))
            data = {
                "to": to,
                "sender": "danielbetzalel16@gmail.com",
                "subject": subject,
                "msg_html": message,
                "msg_plain": message,
                "signature": True
            }
            sent = gmail.send_message(**data)
            return redirect(url_for("user"))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return render_template("send_msg.html")


@app.route('/api/v1/gmail/messages/move_to_garbage', methods=['POST'])
def move_to_garbage(message=None):
    try:
        if not message:
            desired_message_id = request.form['message_id']
        else:
            desired_message_id = message.id
        messages = gmail.get_messages()
        for message in messages:
            if message.id == desired_message_id:
                the_msg = message
        # every msg will be "read" if it goes to the trash
        the_msg.mark_as_read()
        the_msg.trash()
        return redirect(url_for("user"))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/change_label', methods=['POST'])
def change_label():
    try:
        desired_message_id = request.form['message_id']
        desired_label = request.form['wanted_label']

        messages = gmail.get_messages()
        for message in messages:
            if message.id == desired_message_id:
                the_msg = message

        if desired_label == "TRASH":
            move_to_garbage(message=the_msg)

        the_msg.add_label(desired_label)
        return redirect(url_for("user"))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)