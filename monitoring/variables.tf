variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cluster_name" {
  type    = string
  default = "my-eks-cluster"
}

variable "grafana_admin_password" {
  type      = string
  sensitive = true
  default   = "changeme123!"
}
