output "eks_log_group_name"     { value = aws_cloudwatch_log_group.eks_cluster.name }
output "app_log_group_name"     { value = aws_cloudwatch_log_group.application.name }
output "waf_log_group_arn"      { value = aws_cloudwatch_log_group.waf.arn }
output "vpc_flow_log_group_name" { value = aws_cloudwatch_log_group.vpc_flow.name }
