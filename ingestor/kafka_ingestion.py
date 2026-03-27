from utils.kafka_utils import Producer, kafka_config
from utils.conf import consumer_manager
import os
from time import sleep
import logging
from dotenv import load_dotenv
import sys

load_dotenv()

BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia"
PRIM_API_KEY = os.getenv("PRIM_API_KEY","")

LINE_REPORTS_TOPICS  = [
    "line_reports",
    "links",
    "disruptions"
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Add StreamHandler to output to stdout (Docker can capture this)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def main_kafka():
    producer = Producer(kafka_config, PRIM_API_KEY, BASE_URL)
    while True:
        logger.info("Fetching new line reports from PRIM API...")
        producer.ingest_line_reports()

        logger.info("Saving line reports to Kafka topics...")
        for topic in LINE_REPORTS_TOPICS:
            consumer_manager.add_kafka_consumer(topic)
            consumer_manager.upload_to_garage(topic)

        logger.info("Sleeping for 60 seconds before the next fetch...")
        sleep(60)