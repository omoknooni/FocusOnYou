module "api" {
  source = "./api"
  cognito_region = var.cognito_region
  user_pool_id = var.user_pool_id
  app_client_id = var.app_client_id
  aws_region = var.aws_region
  s3_media_bucket_name = var.s3_media_bucket_name
  s3_static_bucket_name = var.s3_static_bucket_name
  dynamodb_table_name = aws_dynamodb_table.job_table.name
}