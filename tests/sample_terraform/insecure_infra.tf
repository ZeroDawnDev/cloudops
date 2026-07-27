provider "aws" {
  region = "us-east-1"
}

# Intentionally insecure S3 bucket for CloudOps AI demo purposes
resource "aws_s3_bucket" "data" {
  bucket = "cloudops-demo-data"
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Wide-open security group
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Allow all inbound traffic"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Oversized, single-instance, no auto scaling
resource "aws_instance" "app" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "m5.4xlarge"

  vpc_security_group_ids = [aws_security_group.web.id]

  tags = {
    Name = "app-server"
  }
}

# RDS with no encryption and a wildcard IAM policy attached elsewhere
resource "aws_db_instance" "main" {
  identifier        = "cloudops-demo-db"
  engine            = "postgres"
  instance_class    = "db.r5.2xlarge"
  allocated_storage = 100
  username          = "admin"
  password          = "SuperSecret123!"
  publicly_accessible = true
  storage_encrypted   = false
  skip_final_snapshot = true
}

resource "aws_iam_policy" "admin_all" {
  name = "full-admin"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}
