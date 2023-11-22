import boto3
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SNS_TOPIC = os.environ['SNS_TOPIC']

rekog = boto3.client('rekognition')
s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamo = boto3.client('dynamodb')

# 비동기식 호출 : face_image가 s3 업로드되면 바로 트리거 or SNS topic
def lambda_handler(event, context):
    # get bucket name and key from event
    noti_message = event['Records'][0]
    logger.info("S3 Notification Record : " + str(noti_message))

    bucket = noti_message['s3']['bucket']['name']
    key = noti_message['s3']['object']['key']

    # make collection if it doesn't exist
    # collectiodID는 job_id로
    collection_id = key.split('/')[0]
    try:
        rekog_response = rekog.create_collection(CollectionId=collection_id)
        if rekog_response['StatusCode'] == 200:
            logger.info('Collection created : '+rekog_response['CollectionArn'])
    except Exception as e:
        print(e)


    # object의 메타데이터에 저장한 얼굴이름 가져오기
    face_name = s3.head_object(Bucket=bucket, Key=key)['Metadata']['face_name']

    # call rekognition to add face to collection
    response = rekog.index_faces(
        CollectionId=collection_id,
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        ExternalImageId=face_name,
        MaxFaces=1,
        QualityFilter="AUTO",
        DetectionAttributes=['ALL']
    )

    # 얼굴 추가 성공시 dynamodb에 저장
    if response['FaceRecords']:
        dynamo.update_item(
            key={
                'job_id': {'S': collection_id}
            },
            UpdateExpression='SET job_status = :job_status',
            ExpressionAttributeValues={":job_status": {'S': 'INDEXED'}}
        )
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # IndexFaces API 실행 후 결과 Publish
    sns_response = sns.publish(
        TopicArn=SNS_TOPIC,
        Message=json.dumps({
            'bucket': bucket,
            "job_id": collection_id,
            'timestamp': timestamp,
            'face_name': face_name,
            'face_id': response['FaceRecords'][0]['Face']['FaceId']
        })
    )

    return {
        'statusCode': 200,
        'MessageId': sns_response['MessageId']
    }
