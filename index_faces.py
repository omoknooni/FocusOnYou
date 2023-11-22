import boto3

rekog = boto3.client('rekognition')
s3 = boto3.client('s3')
# 비동기식 호출 : s3 업로드되면 바로 트리거 or SNS topic


def lambda_handler(event, context):
    # get bucket name and key from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    timestamp = event['Records'][0]['eventTime']

    # make collection if it doesn't exist
    # collectiodID는 job_id로
    collection_id = key.split('/')[0]
    try:
        rekog.create_collection(CollectionId=collection_id)
        print('Collection created')
    except Exception as e:
        print(e)


    # object의 메타데이터에 저장한 얼굴이름 가져오기
    face_name = s3.head_object(Bucket=bucket, Key=key)['Metadata']['face_name']

    # call rekognition to add face to collection
    response = rekog.index_faces(
        CollectionId='mycollection',
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

    # print response
    print(response)
    return response