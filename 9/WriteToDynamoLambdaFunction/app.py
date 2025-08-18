import boto3
import csv
import os
import shutil

env_table = os.environ["TABLE"]

unzipped_dir = "/tmp/unzipped/"
unzipped_s3_prefix = "unzipped/"

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
ddb_table = dynamodb.Table(env_table)

def parse_csv_ddb(app_uuid, details_file):
    # opens the customer details file and extracts the information row by row
    with open(details_file, 'r', encoding="utf-8") as file:
        reader = csv.DictReader(file)
        details_dict = next(reader)
    
    # puts the extracted details in the dynamodb table
    ddb_table.put_item(Item={**details_dict, "APP_UUID": app_uuid})

    return details_dict
    
def lambda_handler(event, context):
    
    try:
        
        # get the bucket and app uuid
        bucket = event["detail"]["bucket"]["name"]
        app_uuid = event["application"]["app_uuid"]
        
        # form the directory of details file
        details_key = f"{unzipped_s3_prefix}{app_uuid}_details.csv"
        details_file = f'/tmp/{app_uuid}_details.csv'
        
        # download the file using the directory and extract details from that file
        s3.download_file(bucket, details_key, details_file)
        parsed_details_dict = parse_csv_ddb(app_uuid, details_file)
        
        
        return {
            "driver_license_id": parsed_details_dict["DOCUMENT_NUMBER"],
            "validation_override": True,
            "app_uuid": app_uuid
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # clean up /tmp/unzipped
        if os.path.exists(unzipped_dir):
            shutil.rmtree(unzipped_dir)
