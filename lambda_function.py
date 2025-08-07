# "Lambda function code to process license, data, and selfie .zip file"

import json
import os
import zipfile
import boto3

unzipped_dir = "/tmp/unzipped/"
unzipped_s3_prefix = "unzipped/"

s3 = boto3.client('s3')

def unzip_object(bucket, key):
    # get the zip file name and set the local path
    zip_name = os.path.basename(key)
    zip_fullpath = f'/tmp/{zip_name}'

    # download the zip file from S3
    s3.download_file(bucket, key, zip_fullpath)
    with zipfile.ZipFile(zip_fullpath, 'r') as zip_ref:
        zip_ref.extractall(unzipped_dir)
    os.remove(zip_fullpath)

    # list all the files in the unzip prefix/folder
    zipped_files = os.listdir(unzipped_dir)
    return zipped_files


def lambda_handler(event, context):
    try:
        print(event)

        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # unzip the object from the bucket using the key to get all the files
        files_list = unzip_object(bucket, key)

        # upload the unzipped files to the unzip prefix in s3
        for file in files_list:
            s3.upload_file(unzipped_dir + file, bucket, unzipped_s3_prefix + file)

        # extract the app_uuid
        app_uuid = os.path.basename(key).replace(".zip", "")

        # extract the selfie_key
        selfie_key = f'{unzipped_s3_prefix}{app_uuid}_selfie.png'

        # extract the license_key
        license_key = f'{unzipped_s3_prefix}{app_uuid}_license.png'

        # extract the details_file
        details_file = f'{unzipped_s3_prefix}{app_uuid}_details.csv'

        # print(f"app_uuid = {app_uuid}")
        # print(f"selfie_key = {selfie_key}")
        # print(f"license_key = {license_key}")
        # print(f"details_file = {details_file}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # clean up /tmp/unzipped
        if os.path.exists(unzipped_dir):
            shutil.rmtree(unzipped_dir)

