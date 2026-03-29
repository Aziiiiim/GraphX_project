from utils.garage_utils import *
from utils.conf import client_minio, KAFKA_CONFIG
from minio.error import S3Error
import os, sys
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

bucket_name = os.getenv("bucket_name")

def download_csv_files():
    for object_name, url in {
        "data/lines_links.csv": "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/traces-du-reseau-ferre-idf/exports/csv",
        "data/stations.csv": "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/emplacement-des-gares-idf/exports/csv"
    }.items():
        try:
            client_minio.stat_object(bucket_name, object_name)
            logger.info(f"Found {object_name} in bucket {bucket_name}.")
        except S3Error as err:
            if err.code == "NoSuchKey":
                logger.info(f"Downloading {object_name}...")
                object_content = download_csv(url)
                upload_csv_to_garage(object_content, object_name, bucket_name)
            else:
                logger.info(f"⚠️ An error occurred: {err}")

def download_zip_files():
    objects = client_minio.list_objects(bucket_name, prefix="tools/", recursive=True)
    first_item = next(objects, None)

    if first_item:
        logger.info(f"Data already imported in bucket {bucket_name}.")
    else:
        logger.info("Folder is empty. Downloading and uploading GTFS data...")
        zip_info = download_zip(
            "https://eu.ftp.opendatasoft.com/stif/GTFS/IDFM-gtfs.zip"
        )
        upload_zip_content_to_garage(zip_info, "data/gtfs", bucket_name)

def main_garage():
    download_csv_files()
    download_zip_files()