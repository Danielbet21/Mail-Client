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
              "label_ids",
              "attachements"]  # TODO: attachements isn't serializable
   
    @staticmethod
    def filter_fields(message, labels_to_list) -> dict:
        return {field: (labels_to_list(message[field]) if field == 'label_ids' else message.get(field)) for field in Constent.fields}
    
    @staticmethod
    def move_to_the_right_label(email,desired_label,desired_message_id,db) -> None:
        db["Users"].update_one({"email":email}, {"$pull": {"UNREAD": desired_message_id}})
        db["Users"].update_one({"email":email}, {"$pull": {"INBOX": desired_message_id}})
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