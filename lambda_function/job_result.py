import boto3
import os
import json
import logging

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo = boto3.client('dynamodb')

FOCUSONYOU_RESULT_BUCKET = os.environ['FOCUSONYOU_RESULT_BUCKET']
BUCKET_REGION=os.environ['BUCKET_REGION']
TABLE_NAME = os.environ['TABLE_NAME']
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
HOOK_URL = os.environ['HOOK_URL']

def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info(f'Message : {message}')

    # parse message
    transjob_status = message.get('state')  # PROGRESSING|COMPLETED|WARNING|ERROR
    transjob_id = message.get('jobId')
    job_id = message.get('input').get('key').split('/')[1]
    output_filename = message.get('outputs')[0].get('key')

    transcoded_video_url = f"https://{FOCUSONYOU_RESULT_BUCKET}.s3.{BUCKET_REGION}.amazonaws.com/{output_filename}"

    if transjob_status == 'COMPLETED':
        dynamo.update_item(
            TableName=TABLE_NAME,  
            Key={
                'job_id': {'S': job_id}
            },
            UpdateExpression="set job_status = :s, transcoded_video = :t",
            ExpressionAttributeValues={
                ':s': {'S': 'TRANSCODE_COMPLETE'},
                ':t': {'S': transcoded_video_url}
            }
        )
        slack_message = {
            'channel': SLACK_CHANNEL,
            'text': f"*[FocusOnYou]*\n\nJob {job_id} has been completed!\nVideo : {transcoded_video_url}"
        } 
        
        req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
        try:
            response = urlopen(req)
            response.read()
            logger.info("Message posted to %s", slack_message['channel'])
        except HTTPError as e:
            logger.error("Request failed: %d %s", e.code, e.reason)
        except URLError as e:
            logger.error("Server connection failed: %s", e.reason)
    elif transjob_status == 'ERROR':
        dynamo.update_item(
            TableName=TABLE_NAME,  
            Key={
                'job_id': {'S': job_id}
            },
            UpdateExpression="set job_status = :s",
            ExpressionAttributeValues={
                ':s': {'S': 'TRANSCODE_FAILED'},
            }
        )
        logger.error(f'Job {transjob_id} is failed')
        logger.error(f'Error message : {message}')
    else:
        logger.info(f'Job {transjob_id} is {transjob_status}')