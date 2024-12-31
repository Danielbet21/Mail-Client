import sqlite3
import base64
from simplegmail import attachment
import logging

logging.basicConfig(level=logging.INFO)

def init_sqlite():
    """Initialize the SQLite database with tables for messages and attachments."""
    conn = sqlite3.connect('attachments.db')
    cursor = conn.cursor()

    # Create table for messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            subject TEXT,
            sender TEXT,
            received_date TEXT
        )''')

    # Create table for attachments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            data BLOB NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages(message_id)
        )''')

    conn.commit()
    conn.close()

def save_message_with_attachments(message_id, attachment):
    """Save message with attachments to the SQLite database."""
    conn = sqlite3.connect('attachments.db')
    cursor = conn.cursor()
        
    if attachment.data: 
        # Save the attachment data as binary (BLOB)
        cursor.execute('''
            INSERT INTO attachments (message_id, filename, data)
            VALUES (?, ?, ?)
        ''', (message_id, attachment.filename, attachment.data))

    conn.commit()
    conn.close()

def get_attachments_by_message_id(message_id):
    """Retrieve attachments for a specific message from the SQLite database."""
    conn = sqlite3.connect('attachments.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT filename, data FROM attachments WHERE message_id = ?
    ''', (message_id,))
    
    result = cursor.fetchall()
    conn.close()
    
    # Prepare the attachments data
    attachments = [
        {
            "filename": row[0],
            "data": row[1]  # Binary data
        }
        for row in result
    ]
    return attachments

def encode_attachment(attachment_data):
    """Encode binary data to base64."""
    return base64.b64encode(attachment_data).decode('utf-8')

def decode_attachment(attachment_data_base64):
    """Decode base64 data back to binary."""
    return base64.b64decode(attachment_data_base64)

def process_attachments(message_id, attachments: list[attachment.Attachment]) -> list[attachment.Attachment]:
    """
    Processes and stores the attachments in SQLite with message_id as the key.
    """
    processed_attachments = []
    
    for att in attachments:
        existing_attachment = get_attachments_by_message_id(message_id)
        
        if existing_attachment:
            processed_attachments.append(existing_attachment)
        else:
            att.download() 
            save_message_with_attachments(message_id, att)
            processed_attachments.append(att)
    return processed_attachments
