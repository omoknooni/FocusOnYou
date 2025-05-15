# S3 bucket for storing videos and images
resource "aws_s3_bucket" "media_bucket" {
  bucket = "focusonyou-media-storage"
  
  tags = {
    Name = "FocusOnYou Media Storage"
  }
}

data "aws_s3_bucket" "static_site" {
    bucket = "focusonyou.omoknooni.me"
}

data "aws_s3_bucket_website_configuration" "static_site" {
    bucket = data.aws_s3_bucket.static_site.id
}

resource "aws_s3_bucket_cors_configuration" "media_bucket_cors" {
    bucket = aws_s3_bucket.media_bucket.id

    cors_rule {
        allowed_headers = [ "*" ]
        allowed_methods = [ "GET", "POST", "PUT" ]
        allowed_origins = [ "http://${data.aws_s3_bucket_website_configuration.website_endpoint}" ]
    }
}


resource "aws_s3_object" "image_folder" {
    bucket = aws_s3_bucket.media_bucket.id
    key = "images/"
}
resource "aws_s3_object" "video_folder" {
    bucket = aws_s3_bucket.media_bucket.id
    key = "videos/"
}

resource "aws_iam_role" "presigned_url_role" {
    name = "focusonyou_presigned_url_role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "lambda.amazonaws.com"
                }
                Sid = ""
            }
        ]
    })
}

resource "aws_iam_policy" "presigned_url_policy" {
    name = "focusonyou_presigned_url_policy"
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
                    "${aws_s3_bucket.media_bucket.arn}/images/*",
                    "${aws_s3_bucket.media_bucket.arn}/videos/*"
                ]
            }
        ]
    })
}

# 인물 사진이 업로드되면 index_face를 트리거 -> 얼굴정보를 collection에 담아야하기에
resource "aws_s3_bucket_notification" "media_bucket_noti" {
    bucket = aws_s3_bucket.media_bucket.id
    lambda_function {
        lambda_function_arn = aws_lambda_function.index_faces.arn
        events = [ "s3:ObjectCreated:Put" ]
        filter_suffix = "images/"
    }
}

# DynamoDB table
resource "aws_dynamodb_table" "job_table" {
  name           = "focusonyou-job-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "job_id"
  
  attribute {
    name = "job_id"
    type = "S"
  }
  
  tags = {
    Name = "FocusOnYou Job Table"
  }
}