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

variable "tags" {
  type    = map(string)
  default = {}
}
