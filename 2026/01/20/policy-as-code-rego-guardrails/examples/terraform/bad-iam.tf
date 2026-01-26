# Example of a non-compliant IAM policy (will be blocked by policy)
resource "aws_iam_role" "example" {
  name = "example-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "example" {
  name = "example-policy"
  role = aws_iam_role.example.id

  # This policy violates multiple rules:
  # 1. Uses wildcard action "*"
  # 2. Uses wildcard resource "*"
  # 3. Uses overly broad service permission "s3:*"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "*"
      Resource = "*"
    }, {
      Effect = "Allow"
      Action = "s3:*"
      Resource = "arn:aws:s3:::my-bucket/*"
    }]
  })
}
