import requests
from kafka import KafkaProducer, KafkaConsumer
from minio import Minio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import io, csv

load_dotenv()
BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia"
PRIM_API_KEY = os.getenv("PRIM_API_KEY","")
kafka_config = {
    'bootstrap_servers': 'kafka1:9092',  # Update with your Kafka broker
    'serializer': lambda v: json.dumps(v).encode('utf-8'),  # Serialize data to JSON
    'deserializer': lambda v: json.loads(v.decode('utf-8'))  # Deserialize data from JSON
}

LINE_REPORTS_TOPICS  = [
    "line_reports",
    "links",
    "disruptions"
]

class Producer:
    def __init__(self, config, auth_token:str, base_url:str):
        self.producer = KafkaProducer(
            bootstrap_servers=config['bootstrap_servers'],
            value_serializer=config['serializer']
        )
        self.auth_token = auth_token
        self.base_url = base_url
        self.start_time = datetime.now().strftime("%Y%m%dT%H%M%S")

    def get(self, url, params = None):
        return requests.get(
            url, 
            params=params, 
            headers={"apiKey": self.auth_token}
        )
    
    def send_to_kafka(self, topics, endpoint, params) -> int:
        response = self.get(f"{self.base_url}/{endpoint}", params)
        if response.status_code == 200:
            data = response.json()
            for topic in topics:
                print(f"Sending {topic} data to kafka")
                self.producer.send(topic, data.get(topic))
                self.producer.flush()
            print(f"Page {data['pagination']['start_page']} of data uploaded to kafka")
            return data['pagination']['total_result']
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return 0
        
    
    def ingest_line_reports(self, count=100):
        params = {
            "since": self.start_time,
            "count": count
        }
        
        total_result = self.send_to_kafka(LINE_REPORTS_TOPICS, "line_reports/line_reports", params)
        for i in range(1, int(total_result)//count+1):
            params['start_page'] = i
            self.send_to_kafka(LINE_REPORTS_TOPICS, "line_reports/line_reports", params)

    def ingest_csv(self, text:str, topic:str):

        cr = csv.DictReader(text.replace('\ufeff', '').splitlines(), delimiter=';')

        for row in cr:
            self.producer.send(topic=topic, value=row)
            self.producer.flush()

# --- Configuration MinIO ---

class ConsumerManager:
    def __init__(self,config):
        self.minio_client = Minio(
            f"{os.getenv('minio_ip_address','localhost')}:3900",
            access_key=os.getenv("key_id"),
            secret_key=os.getenv("secret_key"),
            region="garage",
            secure=False
        )
        self.config = config
        self.bucket_name = os.getenv("bucket_name")
        self.consumers = {}

    def add_kafka_consumer(self, topic: str):
        print(f"Creating consumer for topic: {topic}")
        self.consumers[topic] = KafkaConsumer(
            topic,
            bootstrap_servers=self.config['bootstrap_servers'],
            value_deserializer=self.config['deserializer'],
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            group_id=None,
            consumer_timeout_ms=5000,
        )
        print(f"Consumer created for {topic}")

    def consume_from_kafka(self, topic: str, max_records: int = 5, timeout_ms: int = 5000):
        self.add_kafka_consumer(topic)
        records = self.consumers[topic].poll(timeout_ms=timeout_ms, max_records=max_records)
        message_buffer = []

        for _, messages in records.items():
            for message in messages:
                message_buffer.append(message.value)
                print(message.value)

        if message_buffer:
            return json.dumps(message_buffer).encode('utf-8')
                

    def upload_to_garage(self, topic: str, max_records: int = 5, timeout_ms: int = 5000):
        now = datetime.now()
        file_path = f"data/{topic}/batch_{now.strftime('%Y-%m-%d-%H%M%S')}.json"
        message_buffer = []

        while True:
            records = self.consumers[topic].poll(timeout_ms=timeout_ms, max_records=max_records)
            total = sum(len(messages) for messages in records.values())
            if total == 0:
                break

            print(f"Polled {total} message(s) from {topic}")
            for _, messages in records.items():
                for message in messages:
                    message_buffer.append(message.value)
                    print(message.value)

        if message_buffer:
            try:
                json_data = json.dumps(message_buffer).encode('utf-8')
                self.minio_client.put_object(
                    self.bucket_name,
                    file_path,
                    io.BytesIO(json_data),
                    length=len(json_data),
                    content_type='application/json'
                )
                print(f"[OK] {len(message_buffer)} messages sauvegardés dans : {file_path}")
            except Exception as e:
                print(f"[ERREUR] Impossible d'écrire dans MinIO : {e}")
        else:
            print(f"[INFO] Aucun message reçu pour le topic : {topic}")
