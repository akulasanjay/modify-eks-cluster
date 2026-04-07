output "cluster_name" { value = module.eks.cluster_name }
output "cluster_endpoint" { value = module.eks.cluster_endpoint }
output "vpc_id" { value = module.networking.vpc_id }
output "waf_web_acl_arn" { value = module.waf.web_acl_arn }
output "eks_log_group_name" { value = module.cloudwatch.eks_log_group_name }
output "app_log_group_name" { value = module.cloudwatch.app_log_group_name }
