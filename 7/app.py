import json

def lambda_handler(event, context):
    # TODO implement
    http_event = json.loads(event["body"])
    response = {}
    response["statusCode"] = 200
    response["body"] = http_event["validation_override"]  # true if 3rd-party validation returns true OR false if it returns false
    
    return response
    
