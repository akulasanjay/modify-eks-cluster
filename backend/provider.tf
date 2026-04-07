terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # local backend — this module bootstraps the remote backend, so it stores its own state locally
  backend "local" {}
}

provider "aws" {
  region = var.region
}
