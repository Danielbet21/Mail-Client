from simplegmail import label

"""
messege class
get all the information of the message
mark the message as spam, unread, urgent, garbage
read the messages from the inbox
send a message to the recipient


"""
class message:
    def init(self,
        service: 'googleapiclient.discovery.Resource',
        creds: 'oauth2client.client.OAuth2Credentials',
        user_id: str, msg_id: str, thread_id: str, recipient: str, sender: str, subject: str,
        date: str, snippet, plain: Optional[str] = None, html: Optional[str] = None, 
        label_ids: Optional[List[str]] = None, attachments: Optional[List[Attachment]] = None,
        headers: Optional[dict] = None, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> None:
        self.service = service
        self.creds = creds
        self.user_id = user_id
        self.msg_id = msg_id
        self.thread_id = thread_id
        self.recipient = recipient
        self.sender = sender
        self.subject = subject
        self.date = date
        self.snippet = snippet
        self.plain = plain
        self.html = html
        self.label_ids = label_ids
        self.attachments = attachments
        self.headers = headers
        self.cc = cc
        self.bcc = bcc
            
    
    """
    Display the message
    """
    def toString() ->str :
        return f"Message => From: {self.sender}\nTo: {self.recipient}\n id: {self.id}"
    
    """ 
    All the methods to mark/unmark the message as spam, important, urgent, trash, read, starred
    """    
    def markAsRead(self)-> None:
        self.remove_label(label.UNREAD)
    
    def markAsUnread(self):
        self.add_label(label.UNREAD)
        
    def makeAsImportant(self):
        self.add_label(label.IMPORTANT)
    
    def markAsNotImportant(self):
        self.remove_label(label.IMPORTANT)
        
    def markAsStarred(self):
        self.add_label(label.STARRED)
        
    def markAsNotStarred(self):
        self.remove_label(label.STARRED)
       
    def moveToInbox(self):
        self.add_label(label.INBOX)
            
    def moveToTrash(self):
        self.add_label(label.TRASH)
        
    def  moveFromTrash(self):
        self.remove_label(label.TRASH)
        
    def moveToSpam(self):
        self.add_label(label.SPAM)
    
    def moveFromSpam(self):
        self.remove_label(label.SPAM)  
        
        
        
        """
        service
        creds
        """