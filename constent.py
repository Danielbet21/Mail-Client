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