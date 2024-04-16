from datetime import timedelta
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
import sys
from simplegmail import Gmail
from simplegmail.query import construct_query
import logging

app = Flask(__name__)
app.secret_key = "secret"
gmail = Gmail()
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)


@app.route("/")
def home():
    return redirect(url_for("user", usr="Daniel", messages=[]))


@app.route("/api/v1/gmail/login", methods=["POST", "GET"])
def login():
    pass


@app.route("/api/v1/gmail/logout")
def logout():
    return redirect(url_for("login"))


@app.route("/api/v1/gmail/user/<string:usr>/<messages>")
def user(usr, messages):
    labels = gmail.list_labels()  # get all the labels the current user have
    if messages == "[]":
        messages = get_messages()

    return render_template("user.html", messages=messages, name=usr, labels=labels)


@app.route('/api/v1/gmail/messages', methods=['GET'])
def get_messages():
    try:
        messages = gmail.get_messages()
        return messages
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/<string:str_date>/<string:end_date>', methods=['GET'])
def get_messages_by_date(str_date, end_date):
    try:
        messages = gmail.get_messages(query=f"after={str_date}, before={end_date}")
        return render_template("user.html", messages=messages, name="Daniel")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/<string:source>', methods=['GET'])
def get_messages_by_source(source):
    try:
        messages = gmail.get_messages(query=f"from: {source}")
        return render_template("user.html", messages=messages, name="Daniel")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/unread', methods=['GET'])
def get_unread_messages():
    try:
        messages = gmail.get_unread_inbox()
        return render_template("user.html", messages=messages, name="Daniel")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/<string:wanted_label>', methods=['GET'])
def get_messages_by_label(wanted_label):
    try:
        messages = gmail.get_messages(query=f"label: {wanted_label}")
        return render_template("user.html", messages=messages, name="Daniel")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/send', methods=['POST'])
def send_message():
    try:
        to = request.form['to']
        subject = request.form['subject']
        message = request.form['message']
        data = {
            "to": to,
            "sender": "danielbetzalel16@gmail.com",
            "subject": subject,
            "msg_html": message,
            "msg_plain": message,
            "signature": True
        }
        sent = gmail.send_message(**data)
        redirect("user")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/gmail/messages/move_to_garbage', methods=['POST'])
def move_to_garbage(message):
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
        return redirect(url_for("user", usr="Daniel", messages=[]))
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
        return redirect(url_for("user", usr="Daniel", messages=[]))

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)