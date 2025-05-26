variable "cognito_region" {
  type        = string
  description = "Region for cognito userpool"
}

variable "user_pool_id" {
  type        = string
  description = "Cognito UserPool Id"
}

variable "app_client_id" {
  type        = string
  description = "Cognito APP Client Id"
}

variable "aws_region" {
  type = string
  description = "AWS region to use"
}

variable "s3_media_bucket_name" {
  type = string
  description = "S3 bucket name for media files"
}

variable "s3_static_bucket_name" {
    type = string
    description = "S3 bucket name to static website"
}

variable "dynamodb_table_name" {
  type = string
  description = "DynamoDB table name for job"
}