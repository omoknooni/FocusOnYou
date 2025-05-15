resource "aws_instance" "backend-api" {
  ami           = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (adjust for your region)
  instance_type = "t3a.small"
  subnet_id = tolist(data.aws_subnets.public.ids)[0]
  associate_public_ip_address = true
  tags = {
    Name = "FocusOnYou-Backend"
  }
  
  # IAM role for the instance to access AWS services
  iam_instance_profile = aws_iam_instance_profile.backend_profile.name
}

# 일단 기본 VPC에 배치
data "aws_vpc" "default" {
  default = true
}

# 기본 VPC의 퍼블릭 서브넷 조회
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

# IAM role,policy
resource "aws_iam_role" "backend_role" {
  name = "backend-api-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "backend_profile" {
  name = "backend-api-profile"
  role = aws_iam_role.backend_role.name
}

resource "aws_iam_policy" "backend_api_policy" {
  name        = "media-processing-policy"
  description = "Policy for Rekognition and MediaConvert operations"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:GeneratePresignedUrl"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.media_bucket.arn}",
          "${aws_s3_bucket.media_bucket.arn}/*"
        ]
      },
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
        ]
        Effect   = "Allow"
        Resource = "${aws_dynamodb_table.job_table.arn}"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "media_processing_attachment" {
  role       = aws_iam_role.backend_role.name
  policy_arn = aws_iam_policy.backend_api_policy.arn
}


# MediaConvert endpoint resource
# resource "aws_media_convert_queue" "main_queue" {
#   name        = "focusonyou-main-queue"
#   description = "Main queue for video processing"
  
#   tags = {
#     Name = "FocusOnYou MediaConvert Queue"
#   }
# }