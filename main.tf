module "networking" {
  source               = "./modules/networking"
  cluster_name         = var.cluster_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  tags                 = var.tags
}

module "security_groups" {
  source       = "./modules/security_groups"
  cluster_name = var.cluster_name
  vpc_id       = module.networking.vpc_id
  tags         = var.tags
}

module "iam" {
  source       = "./modules/iam"
  cluster_name = var.cluster_name
}

module "waf" {
  source = "./modules/waf"
  name   = var.cluster_name
  tags   = var.tags
}

module "eks" {
  source             = "./modules/eks"
  cluster_name       = var.cluster_name
  region             = var.region
  kubernetes_version = var.kubernetes_version
  cluster_role_arn   = module.iam.cluster_role_arn
  node_role_arn      = module.iam.node_role_arn
  cluster_sg_id      = module.security_groups.cluster_sg_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids
  node_instance_type = var.node_instance_type
  desired_nodes      = var.desired_nodes
  min_nodes          = var.min_nodes
  max_nodes          = var.max_nodes
  tags               = var.tags

  iam_cluster_policy_arns = [
    module.iam.cluster_role_name,
  ]
  iam_node_policy_arns = [
    module.iam.node_role_name,
  ]
}
