resource "aws_apigatewayv2_api" "http_api" {
  name = "focusonyou-http-api"
  protocol_type = "HTTP"
}

locals {
  lambdas = {
    "POST /jobs/create" = aws_lambda_function.create_job
    "GET /jobs/{job_id}" = aws_lambda_function.get_job
    "GET /jobs" = aws_lambda_function.list_jobs
    "GET /user" = aws_lambda_function.get_user
  }
}

# API에 대한 접근을 Cognito의 JWT를 통해서 제한한
resource "aws_apigatewayv2_authorizer" "cognito_jwt" {
  api_id = aws_apigatewayv2_api.http_api.id
  authorizer_type = "JWT"
  name = "cognito_jwt"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    issuer = "https://cognito-idp.${var.cognito_region}.amazonaws.com/${var.user_pool_id}"
    audience = [var.app_client_id]
  }
}

# Lambda Integration
resource "aws_apigatewayv2_integration" "lambda" {
  for_each = local.lambdas

  api_id = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri = each.value.invoke_arn
  payload_format_version = "2.0"
}

# Lambda route, 앞서 생성한 authorizer 연결
resource "aws_apigatewayv2_route" "lambda" {
  for_each = local.lambdas

  api_id = aws_apigatewayv2_api.http_api.id
  route_key = each.key
  target = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"

  authorizer_id = aws_apigatewayv2_authorizer.cognito_jwt.id
}


# Permission for APIGW to Invoke Lambda
resource "aws_lambda_permission" "apigw" {
  for_each = local.lambdas

  action = "lambda:InvokeFunction"
  principal = "apigateway.amazonaws.com"
  function_name = each.value.function_name
  source_arn = "${aws_apigatewayv2_api.http_api.execution_arn}/*"
}