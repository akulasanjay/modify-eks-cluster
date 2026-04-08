variable "name" {
  description = "Name prefix for WAF resources"
  type        = string
}

variable "alb_arn" {
  description = "ARN of the ALB to associate the WAF with (leave empty to skip association)"
  type        = string
  default     = ""
}

variable "rate_limit" {
  description = "Max requests per 5 minutes per IP before blocking"
  type        = number
  default     = 2000
}

variable "waf_log_group_arn" {
  description = "CloudWatch log group ARN for WAF full logs (must be prefixed aws-waf-logs-)"
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
