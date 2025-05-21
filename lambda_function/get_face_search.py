import boto3
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rekog = boto3.client('rekognition')
dynamo = boto3.client('dynamodb')

TABLE_NAME = os.environ['TABLE_NAME']
MC_ROLEARN = os.environ['MC_ROLE_ARN']
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']

# MediaConvert
mc = boto3.client('mediaconvert')
endpoints = mc.describe_endpoints()['Endpoints'][0]['Url']
mc_client = boto3.client('mediaconvert', endpoint_url=endpoints)

def lambda_handler(event, context):
    # get message from sqs queue
    sqs_message = event['Records'][0]['body']
    logger.info("SQS Message" + str(sqs_message))

    # parse message from sqs queue which contains message from sns
    message = json.loads(sqs_message)
    sns_message = json.loads(message['Message'])
    job_id = sns_message['Video']['S3ObjectName'].split('/')[1]

    # get face_name from dynamodb table
    db_response = dynamo.get_item(
        TableName=TABLE_NAME,
        Key={
            'job_id': {'S': job_id }
        },
    )
    face_name = db_response['Item']['face_name']['S']
    video_name = db_response['Item']['video_filename']['S']

    # GetFaceSearch API 실행
    rekog_response = rekog.get_face_search(
        JobId=sns_message['JobId'],
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
            except KeyError:
                pass
        if 'NextToken' in rekog_response:
            next_token = rekog_response['NextToken']
            rekog_response= rekog.get_face_search(
                JobId=sns_message['JobId'],
                SortBy='INDEX',
                NextToken=next_token
            )
        else:
            break

    dynamo.update_item(
        TableName=TABLE_NAME,
        Key={
            'job_id': {'S': job_id}
        },
        UpdateExpression="SET job_status = :job_status",
        ExpressionAttributeValues={
            ':job_status': {'S': 'GET-SEARCHED'},
        }
    )

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
    

    try:
        # MediaConvert 형식으로 변환
        input_clippings = []
        for start_ms, end_ms in scene_timestamp:
            input_clippings.append({
                'StartTimecode': f"{start_ms/1000:.3f}",
                'EndTimecode':   f"{end_ms/1000:.3f}"
            })

        job_settings = {
            'Inputs': [
                {
                    'FileInputs': f's3://{OUTPUT_BUCKET}/videos',
                    'InputClippings': input_clippings
                }
            ],
            'OutputGroups': [
                {
                    'Name': 'File Group',
                    'OutputGroupSettings': {
                        'Type': 'FILE_GROUP_SETTINGS',
                        'FileGroupSettings': {
                            'Destination': f's3://{OUTPUT_BUCKET}/results/'
                        }
                    },
                    'Outputs': [
                        {
                            'VideoDescription': {
                                'CodecSettings': {
                                    'Codec': 'H_264',
                                    'H264Settings': {
                                        'Bitrate': 1000000,
                                        'MaxBitrate': 10000000,
                                        'RateControlMode': 'CBR',
                                        'SceneChangeDetect': 'TRANSITION_DETECTION'
                                    }
                                },
                                'Width': 1280,
                                'Height': 720,
                                'AfdSignaling': 'NONE',
                                'DropFrameTimecode': 'ENABLED',
                                'RespondToAfd': 'NONE',
                                'ColorMetadata': 'INSERT',
                                'Sharpness': 50,
                                'AntiAlias': 'ENABLED',
                                'TimecodeSource': 'EMBEDDED',
                                'Level': 3,
                                'NameModifier': f"{face_name}"
                            },
                            'AudioDescriptions': [
                                {
                                    'AudioTypeControl': 'FOLLOW_INPUT',
                                    'AudioSourceName': 'Audio Selector 1',
                                    'CodecSettings': {
                                        'Codec': 'AAC',
                                        'AacSettings': {
                                            'Bitrate': 96000,
                                            'EncodingProfile': 'LC',
                                            'RateControlMode': 'CBR',
                                            'CodecProfile': 'LC'
                                        }
                                    },
                                    'LanguageCodeControl': 'FOLLOW_INPUT'
                                }
                            ],
                            'ContainerSettings': {
                                'Container': 'MP4',
                                'Mp4Settings': {
                                    'CslgAtom': 'INCLUDE',
                                    'FreeSpaceBox': 'EXCLUDE',
                                    'MoovPlacement': 'PROGRESSIVE_DOWNLOAD'
                                }
                            },
                            'Extension': 'mp4',
                            'NameModifier': f"{face_name}"
                        }
                    ]
                }
            ]
        }
        
        # MediaConvert Job 생성
        mc_job = mc_client.create_job(
            Role=MC_ROLEARN,
            Settings=job_settings,
            PipelineId=pipeline_id,
            UserMetadata={
                'job_id': job_id
            }
        )

        transjob_id = mc_job['Job']['Id']
        transjob_status = mc_job['Job']['Status']
        logger.info(f'Transcoder job : {transjob_id}')
        logger.info(f'Transcoder job status : {transjob_status}')

        dynamo.update_item(
            TableName=TABLE_NAME,
            Key={
                'job_id': {'S': job_id}
            },
            UpdateExpression="SET job_status = :job_status, transcode_start = :transcode_start",
            ExpressionAttributeValues={
                ':job_status': {'S': 'TRANSCODING'},
                ':transcode_start': {'S': str(datetime.now())}
            }
        )

    except Exception as e:
        logger.error(f'Error creating transcoder job: {e}')
        transjob_id = None
        transjob_status = "EXCEPTIONED"

    return {
        "job_id": job_id,
        "transjob_id": transcoder_job,
        "transjob_status": transjob_status
    }