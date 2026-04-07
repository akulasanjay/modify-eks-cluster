output "cluster_name" { value = module.eks.cluster_name }
output "cluster_endpoint" { value = module.eks.cluster_endpoint }
output "vpc_id" { value = module.networking.vpc_id }
output "waf_web_acl_arn" { value = module.waf.web_acl_arn }
