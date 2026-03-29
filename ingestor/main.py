import logging
from garage_ingestion import main_garage
from kafka_ingestion import main_kafka

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    try:
        main_garage()
    except Exception:
        logging.exception("Garage ingestion failed, continuing with Kafka ingestion")

    main_kafka()