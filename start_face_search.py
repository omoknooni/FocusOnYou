import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FOCUSONYOU_BUCKET = os.environ['FOCUSONYOU_BUCKET']
TABLE_NAME = os.environ['TABLE_NAME']
SNS_TOPIC = os.environ['SNS_TOPIC']
ROLE_ARN = os.environ['ROLE_ARN']

rekog = boto3.client('rekognition')
dynamo = boto3.client('dynamodb')

def lambda_handler(event, context):
    message = event['Records'][0]['Sns']['Message']
    message = json.loads(message)
    logger.info("Message : "+ str(message))    

    job_id = message.get('job_id')
    timestamp = message.get('timestamp')
    face_name = message.get('face_name')
    face_id = message.get('face_id')

    # get video name from dynamodb table
    db_response = dynamo.get_item(
        TableName=TABLE_NAME,
        Key={
            'job_id': {'S': job_id}
        }
    )
    video_name = db_response['Item']['video_name']['S']


    # Start FaceSearch API 실행 후 결과 Publish
    try:
        response = rekog.start_face_search(
            Video={
                'S3Object': {
                    'Bucket': FOCUSONYOU_BUCKET,
                    'Name': 'target-video/' + job_id+'/'+video_name
                }
            },
            CollectionId=job_id,
            NotificationChannel={
                'SNSTopicArn': SNS_TOPIC,
                'RoleArn': ROLE_ARN       # The ARN of an IAM role that gives Amazon Rekognition publishing permissions to the Amazon SNS topic.
            },
            FaceMatchThreshold=90,
        )
        search_id = response['JobId']
        logger.info("SearchId : " + search_id)

        # dynamodb에 search_id 저장
        if search_id:
            dynamo.update_item(
                TableName=TABLE_NAME,
                Key={
                    'job_id': {'S': job_id}
                },
                UpdateExpression='SET search_id = :search_id, job_status = :job_status',
                ExpressionAttributeValues={
                    ':search_id': {'S': search_id},
                    ':job_status': {'S': 'SEARCHED'}
                }
            )

    except Exception as e:
        logger.error(e)