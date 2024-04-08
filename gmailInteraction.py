import sys
import logging

from simplegmail import Gmail

gmail = Gmail()
logging.basicConfig(level=logging.INFO)

"""
mark
Aim:   Mark the message as spam, unread, urgent, garbage 
"""
def mark(messages, index):
    for i in range(len(messages)):
        logging.info("i." + messages[i].sender)
        logging.info(messages[i].subject)
        logging.info("----------------------------------------------------------------------------")

    if index == "1":
        # mark as spam
        # unread
        # urgent
        # garbage
        # back to main
        pass


"""
readMessage
Aim:   Read the messages from the inbox
"""
def readMessage():
    sys.stdout.reconfigure(encoding='utf-8')

    messages: list = gmail.get_unread_inbox()
    # logging.info(messages)
    if len(messages) == 0:
        logging.info("You read all your massages\n")
    else:
        for message in messages:
            logging.info("To: " + message.recipient)
            logging.info("From: " + message.sender)
            logging.info("Subject: " + message.subject)
            logging.info("Date: " + message.date)
            logging.info("Preview: " + message.snippet)
            logging.info("Message Body: " + message.plain + "\n")  # or message.html
    markMenu(messages)

"""
sendMessage
Aim:   Send a message to the recipient
"""
def sendMessage():
    messages = gmail.get_unread_inbox()
    message = messages[0]

    the_msg = input("Enter your message for your recipient:\n")
    params = {
        "to": message.sender,
        "sender": message.recipient,
        "subject": message.subject,
        "msg_html": the_msg,
        "msg_plain": the_msg,
        "signature": True  # use my account signature
    }
    gmail.send_message(**params)  # unpack all the data from params

"""
moveToGarbage
Aim:   Move the message to the garbage
"""
def moveToGarbage():
    sender = input("Enter the sender email:\n")
    str_date = input("Enter the start date of the message (YYYY-MM-DD)\n")
    end_date = input("Enter the end date of the message (YYYY-MM-DD)\n")
    message = gmail.get_messages(query=f"from: {sender}, after={str_date}, before={end_date}")

    if len(message) > 0:
        for msg in message:
            logging.info(msg.sender + "\n" + msg.subject + "\n")
            msg.trash()
            logging.info("Message moved to garbage\n")
    else:
        logging.info("No such messages")