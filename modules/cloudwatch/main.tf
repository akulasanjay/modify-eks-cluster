resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/${var.cluster_name}/cluster"
  retention_in_days = var.retention_days
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/eks/${var.cluster_name}/application"
  retention_in_days = var.retention_days
  tags              = var.tags
}

# WAF full logs — must be prefixed with aws-waf-logs-
resource "aws_cloudwatch_log_group" "waf" {
  name              = "aws-waf-logs-${var.cluster_name}"
  retention_in_days = var.retention_days
  tags              = var.tags
}

# VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow" {
  name              = "/aws/vpc/${var.cluster_name}/flow-logs"
  retention_in_days = var.retention_days
  tags              = var.tags
}

# IAM role for VPC Flow Logs to write to CloudWatch
resource "aws_iam_role" "vpc_flow_logs" {
  name = "${var.cluster_name}-vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "vpc-flow-logs.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "vpc_flow_logs" {
  role = aws_iam_role.vpc_flow_logs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_flow_log" "vpc" {
  vpc_id          = var.vpc_id
  traffic_type    = "ALL"
  iam_role_arn    = aws_iam_role.vpc_flow_logs.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow.arn
  tags            = var.tags
}
