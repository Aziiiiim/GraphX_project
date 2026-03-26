import logging
from garage_ingestion import main_garage
from kafka_ingestion import main_kafka

# Configure logging to see output in Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    main_garage()
    main_kafka()