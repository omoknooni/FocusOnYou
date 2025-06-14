resource "aws_apigatewayv2_api" "http_api" {
  name = "focusonyou-http-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = [ "https://${var.s3_static_bucket_name}" ]
    allow_headers = [ "Authorization", "Content-Type", "X-Amz-Date", "X-Amz-Security-Token", "X-Api-Key", "X-Amz-User-Agent" ]
    allow_methods = [ "*" ]
    allow_credentials = true
    max_age = 300
  }
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

# Lambda route, 앞서 생성한 authorizer 연결, authorization_type과 authorizer_id를 모두 지정해줘야함
resource "aws_apigatewayv2_route" "lambda" {
  for_each = local.lambdas

  api_id = aws_apigatewayv2_api.http_api.id
  route_key = each.key
  target = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"

  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito_jwt.id
}

# 스테이지 생성
resource "aws_apigatewayv2_stage" "name" {
  api_id = aws_apigatewayv2_api.http_api.id
  name = "$default"
  auto_deploy = true
}


# Permission for APIGW to Invoke Lambda
resource "aws_lambda_permission" "apigw" {
  for_each = local.lambdas

  action = "lambda:InvokeFunction"
  principal = "apigateway.amazonaws.com"
  function_name = each.value.function_name
  source_arn = "${aws_apigatewayv2_api.http_api.execution_arn}/*"
}

# # OPTIONS for CORS (route)
# resource "aws_apigatewayv2_route" "cors" {
#   for_each = local.lambdas

#   api_id = aws_apigatewayv2_api.http_api.id
#   route_key = "OPTIONS ${split(" ", each.key)[1]}"
#   target = "integrations/${aws_apigatewayv2_integration.lambda[each.key].id}"
# }

# # OPTIONS for CORS (integration)
# resource "aws_apigatewayv2_integration" "cors" {
#   api_id = aws_apigatewayv2_api.http_api.id
#   integration_type = "AWS_PROXY"
#   template_selection_expression = "$request.method"

#   integration_method = "OPTIONS"
#   passthrough_behavior = "WHEN_NO_MATCH"
#   request_templates = {
#     "OPTIONS" = "{ \"statusCode\": 200 }"
#   }
# }

# # OPTIONS for CORS (response)
# resource "aws_apigatewayv2_integration_response" "cors" {
#   api_id = aws_apigatewayv2_api.http_api.id
#   integration_id = aws_apigatewayv2_integration.cors.id
#   integration_response_key = "/200/"
#   response_templates = {
#     "application/json" = ""
#   }
# }