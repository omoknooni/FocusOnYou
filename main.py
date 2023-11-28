from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pathlib import Path

import boto3
import os, sys
import uuid
import threading

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

s3 = boto3.client("s3",aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),aws_secret_access_key=os.getenv("AWS_SECRET_KEY"))
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

dynamo = boto3.client('dynamodb')
TABLE_NAME = os.getenv("TABLE_NAME")
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


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

## TODO : 업로드 시 progress bar 추가
@app.post("/upload")
async def upload(face_name: str = Form(...), face_image: UploadFile = File(...), target_video: UploadFile = File(...)):
    
    # file extension validation logic
    if not allowed_file(face_image.filename) or not allowed_file(target_video.filename):
        return JSONResponse(status_code=400, content={"message": "Invalid file extension"})

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
            }
        )
        # check the result of put_item
        if db_response['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise Exception("Failed to put item in dynamodb")
        return {"message": "Contents uploaded successfully", "job_id": job_id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    
@app.get("/jobs")
async def list_jobs(request: Request):
    # Retrieve primary key of dynamodb table
    try:
        db_response = dynamo.scan(
            TableName=TABLE_NAME,
            Select='ALL_ATTRIBUTES',
            ProjectionExpression='job_id'
        )

        count = db_response['Count']
        jobs = db_response['Items']
        jobs = [job['job_id']['S'] for job in jobs]
        return templates.TemplateResponse("job_list.html", {"request": request, "jobs": jobs, "count": count})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.get("/jobs/{job_id}")
async def read_job(job_id: str):
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
    return JSONResponse(content={"result": "Complete", "job_id": job_id, "Object": job_obj})