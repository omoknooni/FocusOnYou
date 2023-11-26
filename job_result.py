import boto3
import os
import json
import logging

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo = boto3.client('dynamodb')

TABLE_NAME = os.environ['TABLE_NAME']
SLACK_CHANNEL = os.environ['slackChannel']
HOOK_URL = os.environ['HOOK_URL']

def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info(f'Message : {message}')

    # parse message
    transjob_status = message.get('state')  # PROGRESSING|COMPLETED|WARNING|ERROR
    transjob_id = message.get('jobId')
    pipeline_id = message.get('pipelineId')

    # TODO : job_id를 어떻게 받아올것인가
    job_id = message.get('messageDetails').get('job_id')

    if transjob_status == 'COMPLETED':
        dynamo.update_item(
            TableName=TABLE_NAME,  
            Key={
                'job_id': {'S': job_id}
            },
            UpdateExpression="set job_status = :s",
            ExpressionAttributeValues={
                ':s': {'S': 'TRANSCODE_COMPLETE'},
            }
        )
        slack_message = {
            'channel': SLACK_CHANNEL,
            'text': f"*[FocusOnYou]*\n\nJob {job_id} has been completed!"
        } 
    else:
        slack_message = {
            'channel': SLACK_CHANNEL,
            'text': f"*[FocusOnYou]*\n\nJob {job_id} not completed yet..."
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


    return {
        "statusCode": 200,
    }