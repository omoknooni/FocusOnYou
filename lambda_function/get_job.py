# get_job.py

import os, json
import boto3

AWS_REGION = os.getenv("AWS_REGION")
TABLE_NAME = os.getenv("TABLE_NAME")

dynamo = boto3.client("dynamodb", region_name=AWS_REGION)

def lambda_handler(event, context):
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    job_id = event["pathParameters"].get("job_id")

    try:
        result = dynamo.get_item(
            TableName=TABLE_NAME,
            Key={"job_id": {"S": job_id}},
        )
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"DynamoDB 조회 오류: {str(e)}"}),
        }

    item = result.get("Item")
    if not item:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "작업을 찾을 수 없습니다."}),
        }

    job = {k: list(v.values())[0] for k, v in item.items()}
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(job),
    }
