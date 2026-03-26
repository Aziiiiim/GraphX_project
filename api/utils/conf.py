from minio import Minio
import os, json
from .kafka_utils import ConsumerManager
from dotenv import load_dotenv

load_dotenv()

KAFKA_CONFIG = {
    'bootstrap_servers': 'kafka1:9092',  # Update with your Kafka broker
    'serializer': lambda v: json.dumps(v).encode('utf-8'),  # Serialize data to JSON
    'deserializer': lambda v: json.loads(v.decode('utf-8'))  # Deserialize data from JSON
}

client_minio = Minio(
    f'{os.getenv("minio_ip_address")}:3900',
    access_key=os.getenv("key_id"),
    secret_key=os.getenv("secret_key"),
    secure=False,
    region="garage",
)

consumer_manager = ConsumerManager(
    KAFKA_CONFIG
)