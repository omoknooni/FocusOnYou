# create_job.py

import os, json, uuid
from datetime import datetime
import boto3

REGION     = os.getenv("REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
TABLE_NAME     = os.getenv("TABLE_NAME")

# 미디어 업로드 용량 제한
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 300 * 1024 * 1024  # 300MB

s3     = boto3.client("s3", region_name=REGION)
dynamo = boto3.client("dynamodb", region_name=REGION)

def lambda_handler(event, context):
    # 1) 검증된 JWT 클레임
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    # 필요하다면: username = claims["cognito:username"]

    # 2) 요청 바디 파싱
    body = json.loads(event.get("body", "{}"))
    face_name      = body.get("face_name")
    image_filename = body.get("image_filename")
    image_type     = body.get("image_filetype")
    video_filename = body.get("video_filename")
    video_type     = body.get("video_filetype")

    # 3) 키 생성
    job_id    = str(uuid.uuid4())
    image_key = f"images/{job_id}/{image_filename}"
    video_key = f"videos/{job_id}/{video_filename}"

    # 4) presigned URL 생성
    try:
        image_post = s3.generate_presigned_post(
            Bucket=S3_BUCKET_NAME,
            Key=image_key,
            Fields={"Content-Type": image_type},
            Conditions=[
                ["content-length-range", 1, MAX_IMAGE_SIZE],
                ["starts-with", "$Content-Type", image_type],
            ],
            ExpiresIn=3600,
        )
        video_post = s3.generate_presigned_post(
            Bucket=S3_BUCKET_NAME,
            Key=video_key,
            Fields={"Content-Type": video_type},
            Conditions=[
                ["content-length-range", 1, MAX_VIDEO_SIZE],
                ["starts-with", "$Content-Type", video_type],
            ],
            ExpiresIn=3600,
        )
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Presigned URL 생성 오류: {str(e)}"}),
        }

    # 5) DynamoDB에 저장
    try:
        dynamo.put_item(
            TableName=TABLE_NAME,
            Item={
                "job_id":     {"S": job_id},
                "job_status": {"S": "CREATED"},
                "face_name":  {"S": face_name},
                "image_key":  {"S": image_key},
                "video_key":  {"S": video_key},
                "created_at": {"S": datetime.utcnow().isoformat()},
            },
        )
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"DynamoDB 저장 오류: {str(e)}"}),
        }

    # 6) 응답
    resp = {
        "job_id": job_id,
        "presigned_data": {
            "image": {"url": image_post["url"], "fields": image_post["fields"], "key": image_key},
            "video": {"url": video_post["url"], "fields": video_post["fields"], "key": video_key},
        },
    }
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(resp),
    }
