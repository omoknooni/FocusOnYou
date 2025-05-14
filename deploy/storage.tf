# S3 bucket for storing videos and images
resource "aws_s3_bucket" "media_bucket" {
  bucket = "focusonyou-media-storage"
  
  tags = {
    Name = "FocusOnYou Media Storage"
  }
}

resource "aws_dynamodb_table" "job_table" {
  name           = "focusonyou-job-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "job_id"
  
  attribute {
    name = "job_id"
    type = "S"
  }
  
  tags = {
    Name = "FocusOnYou Job Table"
  }
}