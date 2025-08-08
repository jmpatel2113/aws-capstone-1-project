import boto3
from dotenv import load_dotenv
import os

file_name = "my_s3_object.txt"
object_name = "my_s3_object.txt"

load_dotenv()
bucket_name = os.getenv("DOCUMENT_BUCKET")

s3_client = boto3.client("s3")

response = s3_client.upload_file(file_name, bucket_name, object_name)