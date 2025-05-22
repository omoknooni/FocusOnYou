resource "aws_lambda_function" "job_result" {
    filename = "job_result.zip"
    function_name = "job_result"
    role = aws_iam_role.job_result_role.arn
    handler = "job_result.lambda_handler"
    runtime = "python3.13"
    environment {
        variables = {
            TABLE_NAME = aws_dynamodb_table.job_table.name
            SLACK_CHANNEL = var.slack_channel
            HOOK_URL = var.hook_url
            BUCKET_CDN_URL = aws_cloudfront_distribution.media_bucket_cdn.domain_name
        }
    }
}

data "archive_file" "job_result" {
    type = "zip"
    source_file = "../lambda_function/job_result.py"
    output_path = "job_result.zip"
}

resource "aws_iam_role" "job_result_role" {
    name = "job_result_role"
    assume_role_policy = data.aws_iam_policy_document.lambda_policy.json
}

# EventBridge Rule
resource "aws_cloudwatch_event_rule" "mc_job_complete" {
  name        = "mc-job-complete"
  description = "Catch MediaConvert jobs that have completed"
  event_pattern = <<EOF
{
  "source": ["aws.mediaconvert"],
  "detail-type": ["MediaConvert Job State Change"],
  "detail": {
    "status": ["COMPLETE"]
  }
}
EOF
}

# Eventbridge가 lambda를 트리거
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.mc_job_complete.name
  target_id = "Invoke_job_result"
  arn       = aws_lambda_function.job_result.arn
}

# Lambda가 Eventbridge로부터 호출 허용
resource "aws_lambda_permission" "allow_sns" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.job_result.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.mc_job_complete.arn
}

## 원한다면, Eventbridge -> SNS -> Lambda도 가능

resource "aws_iam_role_policy_attachment" "focusonyou_job_result_dynamodb" {
    role = aws_iam_role.job_result_role.name
    policy_arn = aws_iam_policy.focusonyou_dynamodb.arn
}