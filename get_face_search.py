import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rekog = boto3.client('rekognition')
dynamo = boto3.client('dynamodb')
tscoder = boto3.client('elastictranascoder')

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
        try:
            next_token = rekog_response['NextToken']
            next_search = rekog.get_face_search(
                JobId=message['job_id'],
                SortBy='INDEX',
                NextToken=next_token
            )
        except KeyError:
            break

    # call elastic transcoder to stitch the timestamp and make new video
    transcoder_job = tscoder.create_job(
        ...
    )

    
    return {
        "statusCode": 200
    }