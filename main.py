from fastapi import FastAPI, File, UploadFile, Request, Response, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from botocore.exceptions import ClientError
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

import boto3
import os, sys
import uuid
import threading
from datetime import timedelta
from jose import jwt, JWTError
from fastapi import HTTPException

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

s3 = boto3.client("s3",aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),aws_secret_access_key=os.getenv("AWS_SECRET_KEY"))
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

dynamo = boto3.client('dynamodb', aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),aws_secret_access_key=os.getenv("AWS_SECRET_KEY"), region_name=os.getenv('AWS_REGION'))
TABLE_NAME = os.getenv("TABLE_NAME")

DMO_USERNAME = os.getenv("DMO_USERNAME")
DMO_PASS = os.getenv("DMO_PASS")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

class ProgressPercentage(object):
    def __init__(self, filename, size):
        self._filename = filename
        self._size = size
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self.prog_bar_len = 80

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            ratio = round((float(self._seen_so_far) / float(self._size)) * (self.prog_bar_len - 6), 1)
            current_length = int(round(ratio))

            percentage = round(100 * ratio / (self.prog_bar_len - 6), 1)

            bars = '+' * current_length
            output = bars + ' ' * (self.prog_bar_len - current_length - len(str(percentage)) - 1) + str(percentage) + '%'

            if self._seen_so_far != self._size:
                sys.stdout.write(output + '\r')
            else:
                sys.stdout.write(output + '\n')
            sys.stdout.flush()

ALLOWED_EXTENSION = {'png', 'jpg', 'jpeg', 'mp4', 'flv'}

def allowed_file(filename):
    file_ext = Path(filename).suffix[1:].lower()
    if '.' in filename and file_ext in ALLOWED_EXTENSION:
        return True
    else:
        return False

def create_access_token(data: dict, expires_delta: int):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def auth_token(response: Response, username: str, password: str):
    if username == DMO_USERNAME and password == DMO_PASS:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires.total_seconds()
        )

        response.set_cookie(key="access_token", value=access_token, httponly=True, expires=access_token_expires)
        return True
    else:
        return False

async def get_user(request: Request):
    token = request.cookies.get("access_token")
    if token is None:
        return None
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return {"username": username}
    except JWTError:
        raise credentials_exception

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        response = RedirectResponse(url="/upload", status_code=302)
        validation = await auth_token(response, username, password)

        if not validation:
            return templates.TemplateResponse("login.html", {"request": request, "msg": "Invalid credential"})
        return response
    except HTTPException:
        return templates.TemplateResponse("login.html", {"request": request, "msg": "Invalid credential"})

@app.get("/logout")
async def logout(request: Request):
    response = templates.TemplateResponse("login.html", {"request": request, "msg": "logout Success"})
    response.delete_cookie(key="access_token")
    return response

@app.get("/upload")
async def upload(request: Request):
    user = await get_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("upload.html", {"request": request, "user": user})

@app.post("/upload")
async def upload(request: Request, face_name: str = Form(...), face_image: UploadFile = File(...), target_video: UploadFile = File(...)):
    user = await get_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=302)

    # file extension validation logic
    if not allowed_file(face_image.filename) or not allowed_file(target_video.filename):
        return JSONResponse(status_code=400, content={"message": "Invalid file extension"})

    # file size validation logic
    max_file_size = 250 * 1024 * 1024 # 250MB
    print(f'[*] Check file size : {face_image.size}, {target_video.size}')
    if face_image.size > max_file_size or target_video.size > max_file_size:
        return JSONResponse(status_code=400, content={"message": "File size exceeds 250MB"})

    job_id = str(uuid.uuid4())
    image_object_name = f"face_image/{job_id}/{face_image.filename}"
    target_video_object_name = f"target-video/{job_id}/{target_video.filename}"

    try:
        image_progress = ProgressPercentage(face_image.filename, face_image.size)
        video_progress = ProgressPercentage(target_video.filename, target_video.size)
        
        s3.upload_fileobj(
            face_image.file, 
            S3_BUCKET_NAME, 
            image_object_name, 
            Callback=image_progress, 
            ExtraArgs={
                "Metadata": {
                    "face_name": face_name
                }
            })
        s3.upload_fileobj(target_video.file, S3_BUCKET_NAME, target_video_object_name, Callback=video_progress)
        
        db_response = dynamo.put_item(
            TableName=TABLE_NAME,
            Item={
                'job_id' : {'S': job_id},
                'job_status': {'S': 'UPLOADED'},
                'image_filename' : {'S': face_image.filename},
                'video_filename' : {'S': target_video.filename},
                'face_name' : {'S': face_name},
                'uploaded_at': {'S': str(datetime.now())},
            }
        )
        # check the result of put_item
        if db_response['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise Exception("Failed to put item in dynamodb")
        return RedirectResponse(f"/jobs/{job_id}", status_code=302)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    
@app.get("/jobs")
async def list_jobs(request: Request):
    user = await get_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=302)
    
    # Retrieve primary key of dynamodb table
    try:
        db_response = dynamo.scan(
            TableName=TABLE_NAME,
            Select='SPECIFIC_ATTRIBUTES',
            ProjectionExpression='job_id, uploaded_at'
        )
        count = db_response['Count']
        jobs = db_response['Items']
        jobs = [{'job_id': job['job_id']['S'], 'uploaded_at': job['uploaded_at']['S']} for job in jobs]
        return templates.TemplateResponse("job_list.html", {"request": request, "jobs": jobs, "count": count, "user": user})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.get("/jobs/{job_id}")
async def read_job(request: Request, job_id: str):
    user = await get_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=302)
    
    try:
        db_response = dynamo.get_item(
            TableName=TABLE_NAME,
            Key={
                'job_id': {'S': job_id}
            }
        )
        job_obj = db_response['Item']
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    # return JSONResponse(content={"result": "Complete", "job_id": job_id, "Object": job_obj})
    return templates.TemplateResponse("job_detail.html", {"request": request, "job_id": job_id, "job_obj": job_obj, "user": user})