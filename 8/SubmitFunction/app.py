import os
import json
import requests
import boto3

url = os.environ['INVOKE_URL']
env_table = os.environ['TABLE']
env_topic = os.environ['TOPIC']
env_queue_url = os.environ['QUEUE_URL']

dynamodb = boto3.resource('dynamodb')
ddb_table = dynamodb.Table(env_table)
sns = boto3.client('sns')
sqs = boto3.client('sqs')

def lambda_handler(event, context):

    print("Submitting license data to external validation API...")
    
    message_body = json.loads(event["Records"][0]["body"])
    app_uuid = message_body.pop('uuid')
    print(message_body)
    
    # send data to the external validation API
    try:
        req = requests.post(url, json=message_body, timeout=5)
        req.raise_for_status()
    except requests.RequestException as e:
        print(f"HTTP error: {e}")
        raise
    
    response_json = req.json()
    validation_result = response_json.get("result", False)  # fallback to False if key missing

    # updates dynamodb table with the validation result
    ddb_table.update_item(
        Key={
            'APP_UUID': app_uuid
            },
        UpdateExpression='SET LICENSE_VALIDATION = :v_match',
        ExpressionAttributeValues={
            ':v_match': validation_result
            }
    )
    
    # publish a notification to SNS if validation fails
    if not validation_result:
        sns.publish(
            TopicArn= env_topic,
            Message= 'License validation by third party FAILED',
            Subject='License validation by third party FAILED',
        )
    
    print("License validation completed...")

    
    
    
    

