import boto3
import os
import shutil

env_table = os.environ["TABLE"]
env_topic = os.environ["TOPIC"]

unzipped_dir = "/tmp/unzipped/"
unzipped_s3_prefix = "unzipped/"

rekognition = boto3.client("rekognition")
dynamodb = boto3.resource('dynamodb')
ddb_table = dynamodb.Table(env_table)
sns = boto3.client('sns')


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
    valid_photo = False
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


def lambda_handler(event, context):
    try:
        
        bucket = event["detail"]["bucket"]["name"]
        app_uuid = event["application"]["app_uuid"]
        selfie_key = f'{unzipped_s3_prefix}{app_uuid}_selfie.png'
        license_key = f'{unzipped_s3_prefix}{app_uuid}_license.png'
        
         # match the selfie and the phot in ID
        rekognition_response = compare_faces(app_uuid, bucket, license_key, selfie_key)
        
        if not rekognition_response:
            raise ValueError('Photo rekognition match FAILED. Program will stop')
        else:
            return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # clean up /tmp/unzipped
        if os.path.exists(unzipped_dir):
            shutil.rmtree(unzipped_dir)