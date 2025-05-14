resource "aws_instance" "backend-api" {
  ami           = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (adjust for your region)
  instance_type = "t3.medium"
  
  tags = {
    Name = "FocusOnYou-Backend"
  }
  
  # IAM role for the instance to access AWS services
  iam_instance_profile = aws_iam_instance_profile.backend_profile.name
}

# IAM role and policy for the backend instance
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

# Policy for Rekognition and MediaConvert access
resource "aws_iam_policy" "media_processing_policy" {
  name        = "media-processing-policy"
  description = "Policy for Rekognition and MediaConvert operations"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "rekognition:IndexFaces",
          "rekognition:SearchFacesByImage",
          "rekognition:StartFaceSearch",
          "rekognition:GetFaceSearch",
          "rekognition:CreateCollection",
          "rekognition:DeleteCollection"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "mediaconvert:CreateJob",
          "mediaconvert:GetJob",
          "mediaconvert:ListJobs",
          "mediaconvert:DescribeEndpoints"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.media_bucket.arn}",
          "${aws_s3_bucket.media_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "media_processing_attachment" {
  role       = aws_iam_role.backend_role.name
  policy_arn = aws_iam_policy.media_processing_policy.arn
}


# MediaConvert endpoint resource
resource "aws_media_convert_queue" "main_queue" {
  name        = "focusonyou-main-queue"
  description = "Main queue for video processing"
  
  tags = {
    Name = "FocusOnYou MediaConvert Queue"
  }
}