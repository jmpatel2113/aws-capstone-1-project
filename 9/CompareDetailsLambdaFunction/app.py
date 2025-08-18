import boto3
import os
import csv
import shutil

env_table = os.environ["TABLE"]
env_topic = os.environ["TOPIC"]

unzipped_dir = "/tmp/unzipped/"
unzipped_s3_prefix = "unzipped/"

s3 = boto3.client("s3")
textract = boto3.client("textract")
dynamodb = boto3.resource("dynamodb")
ddb_table = dynamodb.Table(env_table)
sns = boto3.client("sns")

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


def parse_csv_ddb(app_uuid, details_file):
    # opens the customer details file and extracts the information row by row
    with open(details_file, 'r', encoding="utf-8") as file:
        reader = csv.DictReader(file)
        details_dict = next(reader)

    return details_dict
    

def lambda_handler(event, context):
    try:
        
        bucket = event["detail"]["bucket"]["name"]
        app_uuid = event["application"]["app_uuid"]
        license_key = f"{unzipped_s3_prefix}{app_uuid}_license.png"
        
        # form the directory of details file
        details_key = f"{unzipped_s3_prefix}{app_uuid}_details.csv"
        details_file = f'/tmp/{app_uuid}_details.csv'
        
        # download the file using the directory and extract details from that file
        s3.download_file(bucket, details_key, details_file)
        parsed_details_dict = parse_csv_ddb(app_uuid, details_file)
        
        # extract details from ID and compare it with input data entered by customer
        textract_response = extract_details(app_uuid, bucket, license_key, parsed_details_dict)
        if not textract_response:
            raise ValueError('Data comparison between App and license FAILED. Program will stop')
        else:
            return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # clean up /tmp/unzipped
        if os.path.exists(unzipped_dir):
            shutil.rmtree(unzipped_dir)