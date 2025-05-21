# S3 bucket for storing videos and images
resource "aws_s3_bucket" "media_bucket" {
  bucket = var.s3_media_bucket_name
  force_destroy = true
  
  tags = {
    Name = "FocusOnYou Media Storage"
  }
}

# S3 bucket for static website hosting
resource "aws_s3_bucket" "static_site" {
    bucket = var.s3_static_bucket_name
    force_destroy = true

    tags = {
      Name = "FocusOnYou Static Site"
    }
}

# CORS for media bucket (for uploading media)
resource "aws_s3_bucket_cors_configuration" "media_bucket" {
    bucket = aws_s3_bucket.media_bucket.id

    cors_rule {
        allowed_headers = [ "*" ]
        allowed_methods = [ "GET", "POST", "PUT" ]
        allowed_origins = [
            "http://${aws_s3_bucket.static_site.bucket}",
            "https://${aws_s3_bucket.static_site.bucket}",
            "http://${aws_s3_bucket.static_site.bucket}.s3-website.${var.aws_region}.amazonaws.com"
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
                        "AWS:SourceArn" = ["${aws_cloudfront_distribution.media_cdn.arn}"]
                    }
                }
            }
        ]
    })
}
# resource "aws_s3_bucket_website_configuration" "static_site" {
#     bucket = aws_s3_bucket.static_site.id
#     index_document {
#         suffix = "index.html"
#     }
#     error_document {
#       key = "index.html"
#     }
# }

# resource "aws_s3_bucket_public_access_block" "static_site" {
#     bucket = aws_s3_bucket.static_site.id
#     block_public_acls = false
#     block_public_policy = false
#     ignore_public_acls = false
#     restrict_public_buckets = false
# }
# resource "aws_s3_bucket_policy" "static_site" {
#     bucket = aws_s3_bucket.static_site.id
#     policy = jsonencode({
#         Version = "2012-10-17"
#         Statement = [
#             {
#                 Effect = "Allow"
#                 Principal = "*"
#                 Action = [ "s3:GetObject" ]
#                 Resource = [ "${aws_s3_bucket.static_site.arn}/*" ]
#             }
#         ]
#     })
#     depends_on = [ aws_s3_bucket_public_access_block.static_site ]
# }

# resource "aws_s3_bucket_cors_configuration" "media_bucket_cors" {
#     bucket = aws_s3_bucket.media_bucket.id

#     cors_rule {
#         allowed_headers = [ "*" ]
#         allowed_methods = [ "GET", "POST", "PUT" ]
#         allowed_origins = [
#             "http://${aws_s3_bucket.static_site.bucket}",
#             "https://${aws_s3_bucket.static_site.bucket}",
#             "http://${aws_s3_bucket.static_site.bucket}.s3-website.${var.aws_region}.amazonaws.com"
#         ]
#     }
# }

# build static site's resource
# resource "null_resource" "build_and_deploy_frontend" {
#     triggers = {
#       always_run = "${timestamp()}"
#     }
#     provisioner "local-exec" {
#         command = "cd frontend && yarn build && aws s3 sync build/ s3://${aws_s3_bucket.static_site.bucket} --delete"
#     }
# }

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