data "aws_caller_identity" "current" {}

locals {
  s3_bucket_arn = "arn:aws:s3:::${var.s3_media_bucket_name}"
  dynamodb_table_arn = "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.dynamodb_table_name}"

}

resource "aws_lambda_function" "create_job" {
  function_name = "focusonyou-api-createjob"
  filename = "create_job.zip"
  handler = "create_job.lambda_handler"
  runtime = "python3.12"
  role = aws_iam_role.backend_role.arn
  timeout = 10
  environment {
    variables = {
      AWS_REGION = var.aws_region
      S3_BUCKET_NAME = var.s3_media_bucket_name
      TABLE_NAME = var.dynamodb_table_name
    }
  }
}

data "archive_file" "create_job" {
  type = "zip"
  source_file = "../../lambda_function/create_job.py"
  output_path = "create_job.zip"
}

resource "aws_lambda_function" "get_job" {
  function_name = "focusonyou-api-getjob"
  filename = "get_job.zip"
  handler = "get_job.lambda_handler"
  runtime = "python3.12"
  role = aws_iam_role.backend_role.arn
  timeout = 5
  environment {
    variables = {
      AWS_REGION = var.aws_region
      TABLE_NAME = var.dynamodb_table_name
    }
  }
}

data "archive_file" "get_job" {
  type = "zip"
  source_file = "../../lambda_function/get_job.py"
  output_path = "get_job.zip"
}

resource "aws_lambda_function" "list_jobs" {
  function_name = "focusonyou-api-listjobs"
  filename = "list_jobs.zip"
  handler = "list_jobs.lambda_handler"
  runtime = "python3.12"
  role = aws_iam_role.backend_role.arn
  timeout = 10
  environment {
    variables = {
      AWS_REGION = var.aws_region
      TABLE_NAME = var.dynamodb_table_name
    }
  }
}

data "archive_file" "list_jobs" {
  type = "zip"
  source_file = "../../lambda_function/list_jobs.py"
  output_path = "list_jobs.zip"
}

resource "aws_lambda_function" "get_user" {
  function_name = "focusonyou-api-getuser"
  filename = "get_user.zip"
  handler = "get_user.lambda_handler"
  runtime = "python3.12"
  role = aws_iam_role.backend_role.arn
}

data "archive_file" "get_user" {
  type = "zip"
  source_file = "../../lambda_function/get_user.py"
  output_path = "get_user.zip"
}

### Lambda Role
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
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "backend_api_policy" {
  name        = "media-processing-policy"
  description = "Policy for access dynamodb table and media bucket"
  
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
          "${local.s3_bucket_arn}",
          "${local.s3_bucket_arn}/*"
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
        Resource = "${local.dynamodb_table_arn}"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "media_processing_attachment" {
  role       = aws_iam_role.backend_role.name
  policy_arn = aws_iam_policy.backend_api_policy.arn
}