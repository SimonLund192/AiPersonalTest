from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Celery
celery_app = Celery('description_generator',
                    broker=os.getenv('CELERY_BROKER_URL', 'amqp://localhost'),
                    backend=os.getenv('CELERY_RESULT_BACKEND', 'rpc://'))

# Load task modules
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Import tasks after celery_app is created
from . import tasks 