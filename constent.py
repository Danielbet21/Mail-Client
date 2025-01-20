import shared_resources
import pytz
from dateutil import parser
from datetime import datetime, timedelta, timezone

class Constent():
    fields = ["sender", 
              "subject", 
              "date", 
              "snippet",
              "user_id",
              "id",
              "thread_id",
              "recipient",
              "plain", 
              "html",
              "headers",
              "to", 
              "cc",
              "bcc",
              "label_ids"]  


    @staticmethod
    def filter_fields(message, labels_to_list) -> dict:
        return {field: (labels_to_list(message[field]) if field == 'label_ids' else message.get(field)) for field in Constent.fields}
    
        
    @staticmethod
    def handle_token_error(e):
        if "Token has been expired or revoked" in str(e):
            logging.error("Token has been expired or revoked. Refreshing token...")
            try:
                credentials = OAuth2Credentials.from_json(session['credentials'])
                if credentials.access_token_expired:
                    credentials.refresh(httplib2.Http())
                    session['credentials'] = credentials.to_json()
                gmail.list_labels()
            except HttpAccessTokenRefreshError as refresh_error:
                logging.error(f"Failed to refresh token: {refresh_error}")
                return render_template("error.html", message="Failed to refresh token. Please re-authenticate.")
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
                return render_template("error.html", message="An unexpected error occurred. Please try again.")
        else:
            logging.error(f"An unexpected error occurred: {e}")
            return render_template("error.html", message="An unexpected error occurred. Please try again.")


    @staticmethod
    def mark_gmail_message_as_read(message_id,date,subject):
        message_from_gmail = shared_resources.get_message_by_id_from_gmail(message_id,date,subject)
        if message_from_gmail is not None:
            message_from_gmail.mark_as_read()
            
        
    @staticmethod
    def convert_to_utc_plus_3(date_str):
        utc_plus_3 = pytz.timezone('Etc/GMT-3')
        date = parser.isoparse(date_str)
        date_utc_plus_3 = date.astimezone(utc_plus_3)
        
        return date_utc_plus_3
    
    
    @staticmethod
    def get_today_date()-> str:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today = today + timedelta(hours=3)
        return today
    
    
    @staticmethod
    def drop_trash_messages(messages)-> list:
        for message in messages:
            if message["label_ids"] == ["TRASH"]:
                messages.remove(message)
        return messages


    @staticmethod
    def there_is_messages_after_latest_message_from_gmail(gmail, users_collectionn, latest_message_date) -> bool:
        latest_message_date_ = latest_message_date.strftime("%Y/%m/%d")
        messages = gmail.get_messages(query=f"after: {latest_message_date_}")
        if messages and Constent.convert_date_to_utc(messages[0].date) > latest_message_date:
            return True
        return False
    
    
    @staticmethod
    def convert_date_to_utc(date_input)-> datetime:
        if isinstance(date_input, datetime):
            return date_input
        else:
            date = parser.isoparse(date_input)    
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            else:
                date = date.astimezone(timezone.utc)    
            return date
    
    @staticmethod
    def serialize_messages(messages):
        for message in messages:
            message["_id"] = ""
            message["date"] = message["date"].isoformat()
        return messages
            