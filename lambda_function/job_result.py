import boto3
import os
import json
import logging

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo = boto3.client('dynamodb')

BUCKET_CDN_URL = os.environ['BUCKET_CDN_URL']
TABLE_NAME = os.environ['TABLE_NAME']
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
HOOK_URL = os.environ['HOOK_URL']

def lambda_handler(event, context):
    # MediaConvert Job Complete status Event(EventBridge) 
    # https://docs.aws.amazon.com/mediaconvert/latest/ug/ev_status_complete.html
    detail = event['detail']
    logger.info(f'Message : {detail}')

    # parse message
    transjob_status = detail['status']
    transjob_id = detail['jobId']
    job_id = detail['userMetadata']['job_id']
    output_filepath = detail['outputGroupDetails'][0]['outputDetails'][0]['outputFilePaths'][0]
    _, _, bucket, *key_parts = output_filepath.split('/')
    key = '/'.join(key_parts)


    # 최종 사용자가 결과물에 접근할 수 있도록 지정정
    # transcoded_video_url = f"https://{FOCUSONYOU_RESULT_BUCKET}.s3.{BUCKET_REGION}.amazonaws.com/{output_filename}"
    transcoded_video_url = f"https://{BUCKET_CDN_URL}/{key}"

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
    else:
        logger.info(f'Job {transjob_id} is {transjob_status}')