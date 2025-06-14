variable "aws_region" {
    type = string
    description = "AWS region to use"
    default = "us-east-2"
}

variable "s3_media_bucket_name" {
    type = string
    description = "S3 bucket name to save media contents"
}

variable "s3_static_bucket_name" {
    type = string
    description = "S3 bucket name to static website"
}

variable "dynamodb_table_name" {
    type = string
    description = "Table name for Dynamodb"
}

variable "cognito_region" {
    type = string
    description = "Region for cognito userpool"
    default = "us-east-1"
}

variable "user_pool_id" {
    type = string
    description = "Cognito UserPool Id"
}

variable "app_client_id" {
    type = string
    description = "Cognito APP Client Id"
}

variable "docker_image_name" {
    type = string
    description = "Docker image name for backend api"
    default = "omoknooni/focusonyou-backend-api"
}

variable "docker_image_tag" {
    type = string
    description = "Docker image tag for backend api"
    default = "latest"
}

variable "slack_channel" {
    type = string
    description = "slack channel to send job complete msg"
}

variable "hook_url" {
    type = string
    description = "slack webhook url to send job complete msg"
}
