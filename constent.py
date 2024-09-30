import shared_resources
import pytz
from dateutil import parser
from datetime import datetime, timedelta

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
    def move_to_the_right_label(email,desired_label,desired_message_id,db) -> None:
        db["Users"].update_one({"email":email}, {"$pull": {"UNREAD": desired_message_id}})
        db["Users"].update_one({"email":email}, {"$push": {desired_label: desired_message_id}})
        
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
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=3)
        todays_date_str = today.strftime("%Y-%m-%d %H:%M:%S+03:00")
        return todays_date_str
    
    
    @staticmethod
    def drop_trash_messages(messages)-> list:
        for message in messages:
            if message["label_ids"] == ["TRASH"]:
                messages.remove(message)
        return messages
    
    
    @staticmethod
    def get_all_messages_erlier_than_latest_message(message_collection) -> list:
        todays_date = Constent.get_today_date()
        messages  = message_collection.find({"date":{"$gte": todays_date}, "label_ids":{"$ne": "TRASH"}}).sort("date", -1)   
        messages = list(messages)
        return messages
        
    @staticmethod
    def there_is_messages_after_latest_message_from_gmail(gmail, users_collectionn, lastest_message_date) -> bool:
        messages = gmail.get_messages(query=f"after: {lastest_message_date}")
        if messages:
            return True
        return False