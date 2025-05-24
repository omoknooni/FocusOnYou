import boto3
import json, os, uuid
from datetime import datetime

REGION = os.getenv("REGION")
TABLE_NAME = os.getenv("TABLE_NAME")

dynamo = boto3.client("dynamodb", region_name=REGION)

def lambda_handler(event, context):
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]

    try:
        result = dynamo.scan(TableName=TABLE_NAME)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"DynamoDB 조회 오류: {str(e)}"}),
        }

    items = result.get("Items", [])
    jobs = [{k: list(v.values())[0] for k, v in item.items()} for item in items]
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(jobs),
    }