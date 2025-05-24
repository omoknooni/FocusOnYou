# get_user.py

import json

def lambda_handler(event, context):
    claims   = event["requestContext"]["authorizer"]["jwt"]["claims"]
    username = claims.get("cognito:username")

    body = {
        "message": f"Hello {username}",
        "user":    claims,
    }
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
