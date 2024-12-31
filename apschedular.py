from simplegmail import Gmail
from datetime import datetime
import shared_resources
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.base import STATE_RUNNING
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import data_base



class SchedulerManager:
    @staticmethod
    def check_emails(gmail, user_email):
        db = shared_resources.client["Deft"]
        messages = gmail.get_unread_inbox()
        if messages:
            data_base.insert_many_documents_to_collection("Messages", messages)
            messages = [{message.id:data_base.labels_to_list(message.label_ids)} for message in messages]
            for message in messages:
                for id_num, labels in message.items():
                    for label in labels:
                            data_base.insert_id_to_Users_by_label(user_email, label, id_num, db)


    @staticmethod
    def start_scheduler(scheduler: BackgroundScheduler, gmail, user_email):
        # Add a job to the scheduler
        scheduler.add_job(
            func=SchedulerManager.check_emails,
            trigger=IntervalTrigger(minutes=5),  # Run every 5 minutes
            id='check_emails_job',
            name='Check emails every 5 minutes',
            replace_existing=True,
            kwargs={'gmail': gmail, 'user_email': user_email}
        )

        # Start the scheduler if it is not already running
        if scheduler.state != STATE_RUNNING:
            scheduler.start()
