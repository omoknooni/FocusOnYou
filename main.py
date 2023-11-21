from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import boto3
import os

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

s3 = boto3.client("s3",aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"))
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

@app.get("/")
def index():
    return templates.TemplateResponse("index.html", {"request": None})

@app.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    object_name = f"idxfile/{file.filename}"
    try:
        s3.upload_fileobj(file.file, S3_BUCKET_NAME, file.filename)
        return {"message": "File uploaded successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    
@app.get("/jobs")
async def list_jobs():
    # get list of jobs from database
    jobs = {
        {"id": "1a2b3c", "datetime": "2023-11-22 00:40:12"},
        {"id": "4d5e6f", "datetime": "2023-11-22 00:49:30"},
        {"id": "7g8h9i", "datetime": "2023-11-22 00:59:12"},
    }
    return templates.TemplateResponse("job_list.html", {"request": None, "jobs": jobs})
    
@app.get("/jobs/{job_id}")
async def read_job(job_id: str):
    return JSONResponse(content={"job_id": job_id, "status": "conpleted"})