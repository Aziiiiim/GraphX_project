import requests, os
from minio import Minio
from io import BytesIO, StringIO

def download_csv(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.text.replace('\ufeff', '')
    print(f"Downloaded CSV: status={response.status_code}, bytes={len(text.encode('utf-8'))}")
    return text

def upload_csv_to_garage(data: str, file_path: str, bucket_name: str):
    encoded_data = data.encode('utf-8')
    print(f"Uploading CSV: path={file_path}, bytes={len(encoded_data)}")
    bytes_data = BytesIO(encoded_data)
    minio_client = Minio(
        f"{os.getenv('minio_ip_address','localhost')}:3900",
        access_key=os.getenv("key_id"),
        secret_key=os.getenv("secret_key"),
        region="garage",
        secure=False
    )
    minio_client.put_object(
        bucket_name,
        file_path,
        bytes_data,
        length=len(encoded_data),
        content_type='text/csv'
    )