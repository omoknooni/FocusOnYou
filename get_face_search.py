import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rekog = boto3.client('rekognition')
dynamo = boto3.client('dynamodb')
tscoder = boto3.client('elastictranascoder')

pipeline_id = os.environ['PIPELINE_ID']

def lambda_handler(event, context):
    # get message from sqs queue
    sqs_message = event['Records'][0]['body']
    logger.info("SQS Message" + str(sqs_message))

    # parse message from sqs queue which contains message from sns
    message = json.loads(sqs_message)

    # get face_name from dynamodb table
    db_response = dynamo.get_item(
        TableName='face_search_result',
        Key={
            'job_id': {'S': message['job_id']}
        },
    )
    face_name = db_response['Item']['face_name']['S']
    video_name = db_response['Item']['video_filename']['S']

    # GetFaceSearch API 실행
    rekog_response = rekog.get_face_search(
        JobId=message['job_id'],
        SortBy='INDEX'
    )

    detected_timestamp = []

    while True:
        for person in rekog_response['Persons']:
            try:
                for face_matches in person['FaceMatches']:
                    logger.info("Face ID: " + str(face_matches['Face']['FaceId']))
                    logger.info("Face Name: " + str(face_matches['Face']['ExternalImageId']))
                    logger.info("Similarity: " + str(face_matches['Similarity']))

                    # get timestamp of video when the face detected 
                    if face_matches['Face']['ExternalImageId'] == face_name:
                        detected_timestamp.append(person['Timestamp'])

                    # update dynamodb table with face_id, face_name, similarity to dynamodb table
                    dynamo.update_item(
                        TableName='face_search_result',
                        Key={
                            'job_id': {'S': message['job_id']}
                        },
                        UpdateExpression="SET face_id = :face_id, face_name = :face_name, similarity = :similarity, detected_timestamp = :detected_timestamp",
                        ExpressionAttributeValues={
                            ':face_id': {'S': face_matches['Face']['FaceId']},
                            ':face_name': {'S': face_matches['Face']['ExternalImageId']},
                            ':similarity': {'N': str(face_matches['Similarity'])},
                            ':detected_timestamp': {'L': detected_timestamp}
                        }
                    )

            except KeyError:
                pass
        if 'NextToken' in rekog_response:
            next_token = rekog_response['NextToken']
            rekog_response= rekog.get_face_search(
                JobId=message['job_id'],
                SortBy='INDEX',
                NextToken=next_token
            )
        else:
            break

    # convert face search timestamp list to scene level
    scene_timestamp = []
    start = 0
    for i in range(len(detected_timestamp)):
        if start == 0:
            start = end = detected_timestamp[i]
        else:
            if detected_timestamp[i] - end > 1000:
                if end - start >= 1000:
                    scene_timestamp.append((start, end))
                start = 0
            else:
                end = detected_timestamp[i]
    
    if start != 0 and end - start >= 1000:
        scene_timestamp.append((start, end))


    # transform face search timestamp list to transcoder's input format
    detected_timestamp_str = []
    for scene in scene_timestamp:
        start, end = scene
        input = {
            'Key' : video_name,
            'TimeSpan': {
                'StartTime': str(start/1000.),
                'Duration': str((end-start)/1000.)
            },
        }
        detected_timestamp_str.append(input)


    # call elastic transcoder to stitch the timestamp and make new video
    transcoder_job = tscoder.create_job(
        PipelineId=pipeline_id,
        Inputs=detected_timestamp_str,
        Output={
            'Key': 'face_search_result/' + message['job_id'] + '.mp4',
        }
    )

    
    return {
        "statusCode": 200
    }