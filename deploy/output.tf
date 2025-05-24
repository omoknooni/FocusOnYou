output "backend_api_url" {
  value = module.api.backend_api_domain
  description = "The API Gateway domain, Use this value with build frontend (.env REACT_APP_API_URL)"
}

output "static_bucket_name" {
  value = var.s3_static_bucket_name
}