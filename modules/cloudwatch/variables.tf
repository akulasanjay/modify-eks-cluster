variable "cluster_name" {
  type = string
}

variable "vpc_id" {
  description = "VPC ID for flow logs"
  type        = string
}

variable "retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "tags" {
  type    = map(string)
  default = {}
}
