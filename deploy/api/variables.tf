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
