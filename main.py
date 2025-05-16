import os
import uuid
from datetime import datetime, timedelta
from typing import Dict

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError, jwk, jwks_client

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# AWS 클라이언트 설정
s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
)
dynamo = boto3.client(
    "dynamodb",
    region_name=os.getenv("AWS_REGION"),
)

# 설정
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
TABLE_NAME = os.getenv("TABLE_NAME")

# 인증 설정
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "")

# Cognito JWKS URL
JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
jwks_client = jwks_client.JWKSClient(JWKS_URL)
security = HTTPBearer()

# 요청/응답 모델
class CreateJobRequest(BaseModel):
    face_name: str
    image_filename: str
    image_filetype: str
    video_filename: str
    video_filetype: str

class PresignInfo(BaseModel):
    url: str
    key: str

class CreateJobResponse(BaseModel):
    job_id: str
    presigned_urls: Dict[str, PresignInfo]

# 토큰 검증 함수
def verify_cognito_token(token: str) -> dict:
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=APP_CLIENT_ID,
        )
        return claims
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

# 현재 사용자, 공개키를 가져와 토큰 검증
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    claims = verify_cognito_token(token)
    return claims

@app.post("/jobs/create", response_model=CreateJobResponse)
def create_upload_job(
    req: CreateJobRequest,
    user = Depends(get_current_user),
):
    """이미지 및 비디오 업로드를 위한 presigned URL을 생성하고, 작업 정보를 DynamoDB에 저장합니다."""
    job_id = str(uuid.uuid4())
    image_key = f"images/{job_id}/{req.image_filename}"
    video_key = f"videos/{job_id}/{req.video_filename}"

    try:
        image_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": image_key,
                "ContentType": req.image_filetype,
            },
            ExpiresIn=3600,
        )
        video_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": video_key,
                "ContentType": req.video_filetype,
            },
            ExpiresIn=3600,
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Presigned URL 생성 오류: {e}")

    # DynamoDB에 작업 생성
    try:
        dynamo.put_item(
            TableName=TABLE_NAME,
            Item={
                "job_id": {"S": job_id},
                "job_status": {"S": "CREATED"},
                "face_name": {"S": req.face_name},
                "image_key": {"S": image_key},
                "video_key": {"S": video_key},
                "created_at": {"S": datetime.utcnow().isoformat()},
            },
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB 저장 오류: {e}")

    presigned = {
        "image": PresignInfo(url=image_url, key=image_key),
        "video": PresignInfo(url=video_url, key=video_key),
    }
    return CreateJobResponse(job_id=job_id, presigned_urls=presigned)

@app.get("/jobs/{job_id}")
def get_job(job_id: str, user=Depends(get_current_user)):
    """특정 작업의 메타데이터와 상태를 조회합니다."""
    try:
        result = dynamo.get_item(
            TableName=TABLE_NAME,
            Key={"job_id": {"S": job_id}},
        )
        item = result.get("Item")
        if not item:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        # DynamoDB 포맷 변환
        job = {k: list(v.values())[0] for k, v in item.items()}
        return job
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB 조회 오류: {e}")

@app.get("/jobs")
def list_jobs(user=Depends(get_current_user)):
    """모든 작업 목록을 반환합니다."""
    try:
        result = dynamo.scan(TableName=TABLE_NAME)
        items = result.get("Items", [])
        jobs = [{k: list(v.values())[0] for k, v in item.items()} for item in items]
        return jobs
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB 조회 오류: {e}")

# create simple endpoint for authenticated user
@app.get("/user")
def read_root(user=Depends(get_current_user)):
    return {"message": f"Hello {user['cognito:username']}", "user": user}
