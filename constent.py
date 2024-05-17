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
    def filter_fields(message, labels_to_list):
        return {field: (labels_to_list(message[field]) if field == 'label_ids' else message.get(field)) for field in Constent.fields}
    