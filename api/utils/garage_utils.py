import requests, os
from minio import Minio
from io import BytesIO
import zipfile

def download_csv(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.text.replace('\ufeff', '')
    print(f"Downloaded CSV: status={response.status_code}, bytes={len(text.encode('utf-8'))}")
    return text

def download_zip(url: str) -> bytes:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    print(f"Downloaded ZIP: status={response.status_code}, bytes={len(response.content)}")
    return response.content

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

def upload_zip_content_to_garage(data: bytes, path: str, bucket_name: str):
    bytes_data = BytesIO(data)
    minio_client = Minio(
        f"{os.getenv('minio_ip_address','localhost')}:3900",
        access_key=os.getenv("key_id"),
        secret_key=os.getenv("secret_key"),
        region="garage",
        secure=False
    )
    with zipfile.ZipFile(bytes_data) as zip_file:
        for file in zip_file.namelist():
            with zip_file.open(file) as f:
                file_data = f.read()
                print(f"Uploading ZIP entry: {file}, bytes={len(file_data)}")
                minio_client.put_object(
                    bucket_name,
                    f"{path}/{file}",
                    BytesIO(file_data),
                    length=len(file_data),
                    content_type='application/zip'
                )