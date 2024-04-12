import sys
import logging

from simplegmail import Gmail
from simplegmail.query import construct_query


# Create a Gmail
from simplegmail import Gmail
#  object to connect to the Gmail API
gmail = Gmail()
logging.basicConfig(level=logging.INFO)
sys.stdout.reconfigure(encoding='utf-8')


"""
getAllMessages
Aim:    Read the all the messages from the inbox
Output: List of messages
"""
def getAllMessagesFromInbox() -> list:
    messages: list = gmail.get_read_inbox()
    
    if len(messages) == 0:
        logging.info("Your inbox is empty\n")
        return None
    else:
        return messages

""" 
getMessageByDate
Aim:    Read the messages from the inbox by start and end date
Input:  Start Date, end Date
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
Aim:    Read the unread messages from the inbox
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
Aim:    Read the unread messages from the inbox by label
Input:  Wanted Label to search (e.g. SPAM, TRASH, UNREAD, STARRED, SENT, IMPORTANT, DRAFT, PERSONAL, SOCIAL,
        PROMOTIONS, UPDATES, FORUMS and all the custom labels you have created)
Output: List of messages
"""
def getMessageByLabel(wantedLabel: str )-> list:    
    query_params = {
    "unread": True,
    "labels":[[wantedLabel]]
    }

    messages = gmail.get_messages(query=construct_query(query_params))

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
def sendMessage(to: str, subject: str = '', user_id: str = 'me')-> None:

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