# Lambda function
resource "aws_lambda_function" "index_faces" {
    filename = "index_faces.zip"
    function_name = "index_faces"
    role = aws_iam_role.index_faces_role.arn
    handler = "index_faces.lambda_handler"
    runtime = "python3.13"
    environment {
        variables = {
            SNS_TOPIC = aws_sns_topic.index_faces.arn
            TABLE_NAME = aws_dynamodb_table.job_table.name
        }
    }
}

data "archive_file" "index_faces" {
    type = "zip"
    source_file = "../lambda_function/index_faces.py"
    output_path = "index_faces.zip"
}

resource "aws_lambda_function" "start_face_search" {
    filename = "start_face_search.zip"
    function_name = "start_face_search"
    role = aws_iam_role.start_face_search_role.arn
    handler = "start_face_search.lambda_handler"
    runtime = "python3.13"
    environment {
        variables = {
            FOCUSONYOU_BUCKET = aws_s3_bucket.media_bucket.id
            TABLE_NAME = aws_dynamodb_table.job_table.name
            SNS_TOPIC = aws_sns_topic.start_face_search.arn
            ROLE_ARN = aws_iam_role.rekognition_role.arn
        }
    }
}

data "archive_file" "start_face_search" {
    type = "zip"
    source_file = "../lambda_function/start_face_search.py"
    output_path = "start_face_search.zip"
}

resource "aws_lambda_function" "get_face_search" {
    filename = "get_face_search.zip"
    function_name = "get_face_search"
    role = aws_iam_role.get_face_search_role.arn
    handler = "get_face_search.lambda_handler"
    runtime = "python3.13"
    environment {
        variables = {
            TABLE_NAME = aws_dynamodb_table.job_table.name
            MC_ROLEARN = aws_iam_role.mediaconvert_role.arn
            OUTPUT_BUCKET = aws_s3_bucket.media_bucket.id
        }
    }
}

data "archive_file" "get_face_search" {
    type = "zip"
    source_file = "../lambda_function/get_face_search.py"
    output_path = "get_face_search.zip"
}

resource "aws_lambda_function" "job_result" {
    filename = "job_result.zip"
    function_name = "job_result"
    role = aws_iam_role.job_result_role.arn
    handler = "job_result.lambda_handler"
    runtime = "python3.13"
    environment {
        variables = {
            TABLE_NAME = aws_dynamodb_table.job_table.name
        }
    }
}

data "archive_file" "job_result" {
    type = "zip"
    source_file = "../lambda_function/job_result.py"
    output_path = "job_result.zip"
}

# MediaConvert
resource "aws_media_convert_queue" "clip_stitch" {
  name         = "focusonyou-clip-stitch-queue"
  pricing_plan = "ON_DEMAND"
  status       = "ACTIVE"
}

resource "aws_iam_role" "mediaconvert_role" {
    name = "focusonyou_mediaconvert_role"
    assume_role_policy = data.aws_iam_policy_document.lambda_policy.json
}

# Role
resource "aws_iam_role" "index_faces_role" {
    name = "index_faces_role"
    assume_role_policy = data.aws_iam_policy_document.lambda_policy.json
}

resource "aws_iam_role" "start_face_search_role" {
    name = "start_face_search_role"
    assume_role_policy = data.aws_iam_policy_document.lambda_policy.json
}

resource "aws_iam_role" "get_face_search_role" {
    name = "get_face_search_role"
    assume_role_policy = data.aws_iam_policy_document.lambda_policy.json
}

resource "aws_iam_role" "rekognition_role" {
    name = "focusonyou_rekognition_role"
    assume_role_policy = data.aws_iam_policy_document.rekognition_policy.json   
}

resource "aws_iam_role" "job_result_role" {
    name = "job_result_role"
    assume_role_policy = data.aws_iam_policy_document.lambda_policy.json
}

# Policy
resource "aws_iam_policy" "focusonyou_s3" {
    name = "focusonyou_s3"
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = [
                    "s3:GetObject",
                    "s3:PutObject"
                ]
                Effect = "Allow"
                Resource = [
                    aws_s3_bucket.media_bucket.arn,
                    "${aws_s3_bucket.media_bucket.arn}/*"
                ]
            },
            {
                Action = [
                    "s3:ListBucket"
                ]
                Effect = "Allow"
                Resource = [
                    aws_s3_bucket.media_bucket.arn
                ]
            },
            {
                Action = [
                    "s3:ListAllMyBuckets"
                ]
                Effect = "Allow"
                Resource = "*"
            }
        ]
    })
}

resource "aws_iam_policy" "focusonyou_dynamodb" {
    name = "focusonyou_dynamodb"
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:Scan",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query"
                ]
                Effect = "Allow"
                Resource = [
                    aws_dynamodb_table.job_table.arn
                ]
            },
            {
                Effect = "Allow"
                Action = [
                    "dynamodb:ListTables"
                ]
                Resource = "*"
            }
        ]
    })
}

resource "aws_iam_policy" "focusonyou_sns" {
    name = "focusonyou_sns"
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = [
                    "sns:Publish"
                ]
                Effect = "Allow"
                Resource = [
                    aws_sns_topic.index_faces.arn,
                    aws_sns_topic.start_face_search.arn
                ]
            },
            {
                Effect = "Allow"
                Action = [
                    "sns:ListTopics"
                ]
                Resource = "*"
            }
        ]
    })
}

resource "aws_iam_policy" "focusonyou_sqs" {
    name = "focusonyou_sqs"
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = [
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes"
                ]
                Effect = "Allow"
                Resource = [
                    aws_sqs_queue.start_face_search.arn
                ]
            }
        ]
    })
}

resource "aws_iam_policy" "focusonyou_rekognition" {
    name = "focusonyou_rekognition"
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = [
                    "rekognition:CreateCollection",
                    "rekognition:TagResource",
                    "rekognition:IndexFaces",
                    "rekognition:StartFaceSearch"
                ]
                Effect = "Allow"
                Resource = "*"
            }
        ]
    })
}

resource "aws_iam_policy" "mediaconvert" {
    name = "focusonyou_mediaconvert"
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = [
                    "mediaconvert:CreateJob",
                    "mediaconvert:GetJob",
                    "mediaconvert:TagResource"
                ]
                Effect = "Allow"
                Resource = "*"
            }
        ]
    })
}

data "aws_iam_policy_document" "lambda_policy" {
    statement {
        principals {
            type = "Service"
            identifiers = ["lambda.amazonaws.com"]
        }
        actions = [ "sts:AssumeRole" ]
    }
}

data "aws_iam_policy_document" "rekognition_policy" {
    statement {
        principals {
            type = "Service"
            identifiers = ["rekognition.amazonaws.com"]
        }
        actions = [ "sts:AssumeRole" ]
    }
}

# Policy Attachment
# index_faces
resource "aws_iam_role_policy_attachment" "focusonyou_index_faces_s3" {
    role = aws_iam_role.index_faces_role.name
    policy_arn = aws_iam_policy.focusonyou_s3.arn
}

resource "aws_iam_role_policy_attachment" "focusonyou_index_faces_sns" {
    role = aws_iam_role.index_faces_role.name
    policy_arn = aws_iam_policy.focusonyou_sns.arn
}

resource "aws_iam_role_policy_attachment" "focusonyou_index_faces_dynamodb" {
    role = aws_iam_role.index_faces_role.name
    policy_arn = aws_iam_policy.focusonyou_dynamodb.arn
}

resource "aws_iam_role_policy_attachment" "focusonyou_index_faces_rekognition" {
    role = aws_iam_role.index_faces_role.name
    policy_arn = aws_iam_policy.focusonyou_rekognition.arn
}

# start_face_search
resource "aws_iam_role_policy_attachment" "focusonyou_start_face_search_s3" {
    role = aws_iam_role.start_face_search_role.name
    policy_arn = aws_iam_policy.focusonyou_s3.arn
}

resource "aws_iam_role_policy_attachment" "focusonyou_start_face_search_dynamodb" {
    role = aws_iam_role.start_face_search_role.name
    policy_arn = aws_iam_policy.focusonyou_dynamodb.arn
}

resource "aws_iam_role_policy_attachment" "focusonyou_start_face_search_rekognition" {
    role = aws_iam_role.start_face_search_role.name
    policy_arn = aws_iam_policy.focusonyou_rekognition.arn
}

# get_face_search
resource "aws_iam_role_policy_attachment" "focusonyou_get_face_search_dynamodb" {
    role = aws_iam_role.get_face_search_role.name
    policy_arn = aws_iam_policy.focusonyou_dynamodb.arn
}

resource "aws_iam_role_policy_attachment" "focusonyou_get_face_search_sqs" {
    role = aws_iam_role.get_face_search_role.name
    policy_arn = aws_iam_policy.focusonyou_sqs.arn
}

resource "aws_iam_role_policy_attachment" "focusonyou_get_face_search_rekognition" {
    role = aws_iam_role.get_face_search_role.name
    policy_arn = aws_iam_policy.focusonyou_rekognition.arn
}

# rekognition
resource "aws_iam_role_policy_attachment" "focusonyou_rekognition" {
    role = aws_iam_role.rekognition_role.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRekognitionServiceRole"
}

# mediaconvert
resource "aws_iam_role_policy_attachment" "focusonyou_mediaconvert" {
    role = aws_iam_role.mediaconvert_role.name
    policy_arn = aws_iam_policy.mediaconvert.arn
}

# job_result
resource "aws_iam_role_policy_attachment" "focusonyou_job_result_dynamodb" {
    role = aws_iam_role.job_result_role.name
    policy_arn = aws_iam_policy.focusonyou_dynamodb.arn
}

# SNS, SQS
# Rekognition과 연동되는 SNS는 이름 접두사 제약이 있음
resource "aws_sns_topic" "index_faces" {
    name = "AmazonRekognition-index-faces"
}

resource "aws_sns_topic" "start_face_search" {
    name = "AmazonRekognition-start-face-search"
}

resource "aws_sns_topic" "transcode_job" {
    name = "focusonyou-transcode-job"
}

resource "aws_sqs_queue" "start_face_search" {
    name = "AmazonRekognition-start-face-search"
}


# Lambda Event Source Mapping
resource "aws_lambda_event_source_mapping" "get_face_search_trigger" {
    event_source_arn = aws_sqs_queue.start_face_search.arn
    function_name    = aws_lambda_function.get_face_search.arn
}

# SNS Subscription
resource "aws_sns_topic_subscription" "job_result" {
    topic_arn = aws_sns_topic.transcode_job.arn
    protocol = "lambda"
    endpoint = aws_lambda_function.job_result.arn
}

resource "aws_sns_topic_subscription" "get_face_search_sqs" {
    topic_arn = aws_sns_topic.start_face_search.arn
    protocol = "sqs"
    endpoint = aws_sqs_queue.start_face_search.arn
}

resource "aws_sns_topic_subscription" "start_face_search" {
    topic_arn = aws_sns_topic.index_faces.arn
    protocol = "lambda"
    endpoint = aws_lambda_function.start_face_search.arn
}