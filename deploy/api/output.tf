output "backend_api_domain" {
  value = aws_apigatewayv2_stage.staging.invoke_url
  description = "The API Gateway domain, Use this value with build frontend (.env REACT_APP_API_URL)"
}