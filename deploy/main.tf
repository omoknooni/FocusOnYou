module "api" {
  source = "./api"
  cognito_region = var.cognito_region
  user_pool_id = var.user_pool_id
  app_client_id = var.app_client_id
}