variable "kubernetes_version" {
  type    = string
  default = "1.31"
}

variable "cluster_name" {
  type = string
}

variable "region" {
  type = string
}

variable "cluster_role_arn" {
  type = string
}

variable "node_role_arn" {
  type = string
}

variable "cluster_sg_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "node_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "desired_nodes" {
  type    = number
  default = 2
}

variable "min_nodes" {
  type    = number
  default = 2
}

variable "max_nodes" {
  type    = number
  default = 4
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "iam_cluster_policy_arns" {
  type    = list(string)
  default = []
}

variable "iam_node_policy_arns" {
  type    = list(string)
  default = []
}
