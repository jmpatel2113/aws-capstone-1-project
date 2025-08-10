# "Lambda function code to process license, data, and selfie .zip file"

import json
import os
import zipfile
import boto3
import shutil
import csv

# Environment variables:
# TABLE = CustomerMetaDataTable

unzipped_dir = "/tmp/unzipped/"
unzipped_s3_prefix = "unzipped/"
env_table = os.environ["TABLE"]
env_topic = os.environ['TOPIC']

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
ddb_table = dynamodb.Table(env_table)
rekognition = boto3.client('rekognition')
sns = boto3.client('sns')
textract = boto3.client('textract')


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


def parse_csv_ddb(app_uuid, details_file):
    # opens the customer details file and extracts the information row by row
    with open(details_file, 'r', encoding="utf-8") as file:
        reader = csv.DictReader(file)
        details_dict = next(reader)
    
    # puts the extracted details in the dynamodb table
    ddb_table.put_item(Item={**details_dict, "APP_UUID": app_uuid})

    return details_dict
    

def compare_faces(app_uuid, bucket, license_key, selfie_key):
    
    print("started comparing faces")
    # uses rekognition to compare selfie and license photo that is stored in an S3 bucket
    response = rekognition.compare_faces(
        SourceImage={'S3Object': {
            'Bucket': bucket,
            'Name': license_key,
        }},
        TargetImage={'S3Object': {
            'Bucket': bucket,
            'Name': selfie_key,
        }},
        SimilarityThreshold=80
    )
    
    # checks if the photo comparison is valid
    valid_photo = False;
    if(len(response["FaceMatches"]) < 1):
        valid_photo = False
    elif(response["FaceMatches"][0]["Similarity"] < 80):
        valid_photo = False
    else:
        valid_photo = True
        
    # update the dynamodb table depending on the comparison result
    ddb_table.update_item(
        Key={
            "APP_UUID": app_uuid
        }, 
        UpdateExpression='SET LICENSE_SELFIE_MATCH = :p_match', 
        ExpressionAttributeValues={
            ':p_match': valid_photo
        }
    )
    
    # if the photo does not match, customer is notified through this SNS topic
    if not valid_photo:
        sns.publish(
            TopicArn= env_topic,
            Message= 'License photo validation FAILED',
            Subject='License photo validation FAILED',
            )

    print("finished compare faces")
    return valid_photo
    
    
def extract_details(app_uuid, bucket, license_key, parsed_details_dict):
    
    print("Starting to extract details from ID...")
    # uses Textract to analyze the ID
    response= textract.analyze_id(
        DocumentPages=[
            {
                "S3Object":{
                    "Bucket": bucket,
                    "Name": license_key
                }
            }
        ]
    )
    
    # extracts the details after analysis
    id_document = response["IdentityDocuments"][0]
    id_data = id_document["IdentityDocumentFields"]
    id_fields = {}
    
    csv_fields = ['DOCUMENT_NUMBER','FIRST_NAME','LAST_NAME','DATE_OF_BIRTH', 'ADDRESS','STATE_IN_ADDRESS','CITY_IN_ADDRESS','ZIP_CODE_IN_ADDRESS']
    for data_field in id_data:
        field = data_field["Type"]["Text"]
        if field in csv_fields:
            id_fields[field] = data_field["ValueDetection"]["Text"]
    
    # compare the extracted data from ID and input data from customer
    # strict comparison
    valid_comparison = parsed_details_dict == id_fields
    
    # flexible comparison
    # valid_comparison = all(
    #     parsed_details_dict.get(k, '').strip().lower() == id_fields.get(k, '').strip().lower()
    #     for k in csv_fields
    # )

    
    # update the comparison result in the database
    ddb_table.update_item(
        Key={
            "APP_UUID": app_uuid
        }, 
        UpdateExpression='SET LICENSE_DETAILS_MATCH = :d_match', 
        ExpressionAttributeValues={
            ':d_match': valid_comparison
        }
    )
    
    # notify the customer if the comparison does not match
    if not valid_comparison:
        sns.publish(
            TopicArn= env_topic,
            Message= 'Data validation between the license and the .csv file FAILED',
            Subject='Data validation between the license and the .csv file FAILED',
            )

    print("finished extracting and comparing details from ID and input data")
    return valid_comparison
    

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
        details_file = f'{unzipped_dir}{app_uuid}_details.csv'

        # print(f"app_uuid = {app_uuid}")
        # print(f"selfie_key = {selfie_key}")
        # print(f"license_key = {license_key}")
        # print(f"details_file = {details_file}")
    
        parsed_details_dict = parse_csv_ddb(app_uuid, details_file)
        # print(parsed_details_dict)
        
        # match the selfie and the phot in ID
        rekognition_response = compare_faces(app_uuid, bucket, license_key, selfie_key)
        if not rekognition_response:
            raise ValueError('Photo rekognition match FAILED. Program will stop')
        
        # extract details from ID and compare it with input data entered by customer
        textract_response = extract_details(app_uuid, bucket, license_key, parsed_details_dict)
        if not textract_response:
            raise ValueError('Data comparison between App and license FAILED. Program will stop')
    
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # clean up /tmp/unzipped
        if os.path.exists(unzipped_dir):
            shutil.rmtree(unzipped_dir)

