output "backend_api_url" {
  value = aws_instance.backend-api.public_dns
}

output "static_bucket_name" {
  value = var.s3_static_bucket_name
}