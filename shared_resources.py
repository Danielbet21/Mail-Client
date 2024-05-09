import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")



def get_name_from_email(email) -> str:

    return str(email.split('@')[0])


def get_labels(labels, indicator:int)-> list:
    # indicator = 0 :from gmail, 1: from mongo
    if indicator == 0:
        labels = labels.split(',')
        label_names = [label.split("'")[1] for label in labels]
        label_names = list(set(label_names))
    else:
        label_names = [label.name for label in labels]

    
    return label_names