# S3 bucket for storing videos and images
resource "aws_s3_bucket" "media_bucket" {
  bucket = var.s3_media_bucket_name
  force_destroy = true
  
  tags = {
    Name = "FocusOnYou Media Storage"
  }
}

# S3 bucket for static website hosting
data "aws_s3_bucket" "static_site" {
    bucket = var.s3_static_bucket_name
}

# CORS for media bucket (for uploading media)
resource "aws_s3_bucket_cors_configuration" "media_bucket" {
    bucket = aws_s3_bucket.media_bucket.id

    cors_rule {
        allowed_headers = [ "*" ]
        allowed_methods = [ "GET", "POST", "PUT" ]
        allowed_origins = [
            "http://${data.aws_s3_bucket.static_site.bucket}",
            "https://${data.aws_s3_bucket.static_site.bucket}",
            "http://${data.aws_s3_bucket.static_site.bucket}.s3-website.${var.aws_region}.amazonaws.com"
        ]
    }
}


# media bucket은 cloudfront distribution으로만 접근가능하게
resource "aws_s3_bucket_policy" "media_bucket" {
    bucket = aws_s3_bucket.media_bucket.id
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Sid = "AllowCloudfront"
                Effect = "Allow"
                Principal = {
                    Service = "cloudfront.amazonaws.com"
                }
                Action = [ "s3:GetObject" ]
                Resource = [ "${aws_s3_bucket.media_bucket.arn}/*" ]
                Condition = {
                    StringLike = {
                        "AWS:SourceArn" = "${aws_cloudfront_distribution.media_bucket_cdn.arn}"
                    }
                }
            }
        ]
    })
}

resource "aws_s3_object" "image_folder" {
    bucket = aws_s3_bucket.media_bucket.id
    key = "images/"
}
resource "aws_s3_object" "video_folder" {
    bucket = aws_s3_bucket.media_bucket.id
    key = "videos/"
}

resource "aws_s3_object" "result_folder" {
    bucket = aws_s3_bucket.media_bucket.id
    key = "results/"
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

resource "aws_lambda_permission" "allow_bucket" {
    statement_id = "AllowExecutionFromS3Bucket"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.index_faces.function_name
    principal = "s3.amazonaws.com"
    source_arn = aws_s3_bucket.media_bucket.arn
}

# 인물 사진이 업로드되면 index_face를 트리거 -> 얼굴정보를 collection에 담아야하기에
resource "aws_s3_bucket_notification" "media_bucket_noti" {
    bucket = aws_s3_bucket.media_bucket.id
    lambda_function {
        lambda_function_arn = aws_lambda_function.index_faces.arn
        events = [ "s3:ObjectCreated:Put" ]
        filter_prefix = "images/"
    }
    depends_on = [ aws_lambda_permission.allow_bucket ]
}

# DynamoDB table
resource "aws_dynamodb_table" "job_table" {
  name           = var.dynamodb_table_name
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