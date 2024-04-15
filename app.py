from datetime import timedelta
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
import sys
from simplegmail import Gmail
from simplegmail.query import construct_query

app = Flask(__name__)
app.secret_key = "secret"
gmail = Gmail()
sys.stdout.reconfigure(encoding='utf-8')


@app.route("/")
def home():
    return get_messages_by_label("IMPORTANT")


@app.route("/api/v1/gmail/login", methods=["POST", "GET"])
def login():
    pass


@app.route("/api/v1/gmail/logout")
def logout():
    return redirect(url_for("login"))


@app.route("/api/v1/gmail/user")
def user(usr):
    messages = get_messages()
    return render_template("user.html", name=usr, messages=messages)


@app.route('/api/v1/gmail/messages', methods=['GET'])
def get_messages():
    try:
        messages = gmail.get_messages()
        return render_template("user.html", messages=messages, name="Daniel")
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


if __name__ == "__main__":
    app.run(debug=True)