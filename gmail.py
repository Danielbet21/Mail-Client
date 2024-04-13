import sys
import logging

from simplegmail import Gmail
from simplegmail.query import construct_query

#  object to connect to the Gmail API
gmail = Gmail()
logging.basicConfig(level=logging.INFO)
sys.stdout.reconfigure(encoding='utf-8')


"""
getAllMessages
Aim:    Get the all the messages from the inbox
Output: List of messages
"""
def getAllMessagesFromInbox() -> list:
    messages: list = gmail.get_messages()
    
    if len(messages) == 0:
        logging.info("Your inbox is empty\n")
        return None
    else:
        return messages

""" 
getMessageByDate
Aim:    Read the messages from the inbox by start and end date
Input:  Start Date, end Date (DATE FORMAT: "YYYY/MM/DD")
Output: List of messages
"""
def getMessageByDate(strDate: str, endDate: str)-> list:
    messages: list = gmail.get_messages(query=f"after={strDate}, before={endDate}")

    if len(messages) == 0:
        logging.info("No messages found\n")
        return None
    else:
        return messages
   

"""
getMessegeBySource
Aim:    Get all the messages from the inbox by source  email address 
Input:  Email source 
Output: List of messages
"""
def getMessegeBySource(source: str)->list:
    messages = gmail.get_messages(query=f"from:{source}")
    if len(messages) == 0:
        logging.info("No messages found\n")
        return None
    else:
        return messages


"""
getUnreadMessages
Aim:    Read the unread messages from the inbox, and mark them as read
Output: list of messages
"""
def getUnreadMessages()-> list:
    messages: list = gmail.get_unread_inbox()
    
    if len(messages) == 0:
        logging.info("You've read all your messages!\n")
        return None
    else:
        return messages


"""
getMessageByLabel
Aim:    Read the messages from the inbox by label
Input:  Wanted Label to search (e.g. SPAM, TRASH, UNREAD, STARRED, SENT, IMPORTANT, DRAFT, PERSONAL, SOCIAL,
        PROMOTIONS, UPDATES, FORUMS and all the custom labels you have created)
        unread: True or False to search only the unread messages or not
Output: List of messages
"""
def getMessageByLabel(wantedLabel: str , unread: bool)-> list: 
    query_params = {
        "labels":[[wantedLabel]]
    }
    messages = gmail.get_messages(query=construct_query(query_params))
    # if unread is True, then filter the unread messages
    if unread:
        messages = [message for message in messages if 'UNREAD' in message.label_ids]

    if len(messages) == 0:
        logging.info("No messages found\n")
        return None
    else:
        return messages
   
    
"""
sendMessage
Aim:   Send a message to the recipient
Input: To, subject, user_id
"""
def sendMessage(to: str, subject: str = '', me: str = "danielbetzalel16@gmail.com")-> None:

    # the_msg = input("Enter your message for your recipient:\n")
    the_msg = "Hello, this is a test message"
    params = {
        "to": to,
        "sender": me,
        "subject": subject,
        "msg_html": the_msg,
        "msg_plain": the_msg,
        "signature": True  # use my account signature
    }
    gmail.send_message(**params)  # unpack all the data from params
    logging.info("Message sent\n")


"""
moveToGarbage
Aim:   Move the message to the garbage
Input: source, start date, end date
"""
def moveToGarbage(source: str, strDate: str, endDate: str)-> None:  
    message = gmail.get_messages(query=f"from: {sender}, after={str_date}, before={end_date}")

    if len(message) > 0:
        for msg in message:
            logging.info(msg.sender + "\n" + msg.subject + "\n")
            msg.trash()
            logging.info("Message moved to garbage\n")
    else:
        logging.info("No such messages")
        return


"""
markAsSpam
Aim:   Mark the email as spam
Input: Message object
"""
def markAsSpam(message)-> int:
    message.mark_as_spam()
    return 1
   

"""
markAsImportant
Aim:   Mark the email as urgent
Input: Message object
"""
def markAsImportant(message)-> int:
    message.mark_as_important()
    return 1



"""
functions i need to implement
delete_labal
create_label
list_labels
"""