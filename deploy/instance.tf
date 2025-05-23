data "aws_ami" "ubuntu" {
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = [ "099720109477" ]
}

resource "aws_instance" "backend-api" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3a.small"
  subnet_id = tolist(data.aws_subnets.public.ids)[0]
  associate_public_ip_address = true

  vpc_security_group_ids = [ aws_security_group.backend_sg.id ]
  key_name = aws_key_pair.backend_key.key_name

  user_data = <<EOF
#!/bin/bash
apt-get update
echo "[*] Install Docker & Docker compose"
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
docker -v

curl -L https://github.com/docker/compose/releases/download/v2.36.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose -v

echo "[*] Create app dir"
mkdir -p /app/backend
cd /app/backend

echo "[*] Get Docker-compose.yml"
cat > docker-compose.yml << EOD
version: '3.8'

services:
  fastapi:
    image: ${var.docker_image_name}:${var.docker_image_tag}
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: always
EOD

echo "[*] Get env for App"
cat > .env << EOE
AWS_REGION=${var.aws_region}
S3_BUCKET_NAME=${var.s3_media_bucket_name}
TABLE_NAME=${var.dynamodb_table_name}
COGNITO_REGION=${var.cognito_region}
COGNITO_USER_POOL_ID=${var.user_pool_id}
COGNITO_APP_CLIENT_ID=${var.app_client_id}
EOE

echo "[*] Start Backend Service"
docker-compose -p focusonyou up -d
EOF
  tags = {
    Name = "FocusOnYou-Backend"
  }
  
  # IAM role for the instance to access AWS services
  iam_instance_profile = aws_iam_instance_profile.backend_profile.name
}

# 일단 기본 VPC에 배치
data "aws_vpc" "default" {
  default = true
}

# 기본 VPC의 퍼블릭 서브넷 조회
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

# IAM role,policy
resource "aws_iam_role" "backend_role" {
  name = "backend-api-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "backend_profile" {
  name = "backend-api-profile"
  role = aws_iam_role.backend_role.name
}

resource "aws_iam_policy" "backend_api_policy" {
  name        = "media-processing-policy"
  description = "Policy for access dynamodb table and media bucket"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:GeneratePresignedUrl"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.media_bucket.arn}",
          "${aws_s3_bucket.media_bucket.arn}/*"
        ]
      },
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
        ]
        Effect   = "Allow"
        Resource = "${aws_dynamodb_table.job_table.arn}"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "media_processing_attachment" {
  role       = aws_iam_role.backend_role.name
  policy_arn = aws_iam_policy.backend_api_policy.arn
}

# SSH 키 페어 생성
resource "aws_key_pair" "backend_key" {
  key_name   = "focusonyou-backend-key"
  public_key = var.ssh_public_key
}

# 보안 그룹 생성
resource "aws_security_group" "backend_sg" {
  name        = "focusonyou-backend-sg"
  description = "Security group for backend API"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "API access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "FocusOnYou-Backend-SG"
  }
}