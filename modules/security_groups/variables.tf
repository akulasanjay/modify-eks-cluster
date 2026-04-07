variable "cluster_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "admin_cidr" {
  type    = string
  default = "203.0.113.0/24"
}

variable "tags" {
  type    = map(string)
  default = {}
}
