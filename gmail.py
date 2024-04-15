import sys
import logging

from simplegmail import Gmail
from simplegmail.query import construct_query

gmail = Gmail()
logging.basicConfig(level=logging.INFO)
sys.stdout.reconfigure(encoding='utf-8')


def get_all_messages_from_inbox() -> list:
    """
    Aim:    Get the all the messages from the inbox
    Output: List of messages
    """
    messages = gmail.get_messages()
    
    if len(messages) == 0:
        logging.info("Your inbox is empty\n")
       
    return messages

def get_message_by_date(str_date: str, end_date: str)-> list:
    """
    Aim:    Read the messages from the inbox by start and end date
    Input:  Start Date, end Date (DATE FORMAT: "YYYY/MM/DD")
    Output: List of messages
    """
    messages = gmail.get_messages(query=f"after={str_date}, before={end_date}")

    if len(messages) == 0:
        logging.debug("No messages found")
    
    return messages

def get_message_by_source(source: str)->list:
    """
    Aim:    Get all the messages from the inbox by source  email address 
    Input:  Email source 
    Output: List of messages
    """
    messages = gmail.get_messages(query=f"from:{source}")
    if len(messages) == 0:
        logging.debug("No messages found")

    return messages

def get_unread_messages()-> list:
    """
    Aim:    Read the unread messages from the inbox, and mark them as read
    Output: list of messages
    """
    messages = gmail.get_unread_inbox()
    
    if len(messages) == 0:
                logging.debug("You've read all your messages!")
    return messages

def get_message_by_label(wanted_label: str , unread: bool)-> list: 
    """
    Aim:    Read the messages from the inbox by label
    Input:  Wanted Label to search (e.g. SPAM, TRASH, UNREAD, STARRED, SENT, IMPORTANT, DRAFT, PERSONAL, SOCIAL,
            PROMOTIONS, UPDATES, FORUMS and all the custom labels you have created)
            unread: True or False to search only the unread messages or not
    Output: List of messages
    """
    query_params = {
        "labels":[[wanted_label]]
    }
    messages = gmail.get_messages(query=construct_query(query_params))
    # if unread is True, then filter the unread messages
    if unread:
        messages = [message for message in messages if 'UNREAD' in message.label_ids]

    if len(messages) == 0:
        logging.debug("No messages found")
    
    return messages

def send_message(to: str, subject: str = '', me: str = "danielbetzalel16@gmail.com")-> None:
    """
    Aim:   Send a message to the recipient
    Input: To, subject, user_id
    """
    the_msg = "Hello, this is a test message"
    params = {
        "to": to,
        "sender": me,
        "subject": subject,
        "msg_html": the_msg,
        "msg_plain": the_msg,
        "signature": True  
    }
    gmail.send_message(**params)  # unpack all the data from params
    logging.debug("Message sent")

def move_to_garbage(source: str, str_date: str, end_date: str)-> None:  
    """
    Aim:   Move the message to the garbage
    Input: source, start date, end date
    """
    message = gmail.get_messages(query=f"from: {source}, after={str_date}, before={end_date}")

    if len(message) > 0:
        for msg in message:
            logging.info(msg.sender + "\n" + msg.subject + "\n")
            msg.trash()
            logging.info("Message moved to garbage")
    else:
         logging.debug("No such messages")
         

def mark_as_spam(message)-> None:
    """
    Aim:   Mark the email as spam
    Input: Message object
    """
    message.mark_as_spam()

def mark_as_important(message)-> None:
    """
    Aim:   Mark the email as urgent
    Input: Message object
    """
    message.mark_as_important()

def delete_label(message , label: str)-> None:
    """
    Aim:   Delete the label
    """
    message.remove_label(label)
    logging.debug("Label deleted")
"""
functions i need to implement
delete_labal
create_label
list_labels
"""