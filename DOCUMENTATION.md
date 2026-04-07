# EKS Cluster Project — Technical Documentation

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Architecture](#3-architecture)
4. [Module: backend](#4-module-backend)
5. [Module: networking](#5-module-networking)
6. [Module: security_groups](#6-module-security_groups)
7. [Module: iam](#7-module-iam)
8. [Module: eks](#8-module-eks)
9. [Module: waf](#9-module-waf)
10. [Module: cloudwatch](#10-module-cloudwatch)
11. [Module: monitoring](#11-module-monitoring)
12. [Variables Reference](#12-variables-reference)
13. [Deployment Guide](#13-deployment-guide)
14. [Teardown Guide](#14-teardown-guide)
15. [Known Issues & TODOs](#15-known-issues--todos)

---

## 1. Project Overview

This project provisions a fully functional Amazon EKS cluster on AWS using Terraform, including:

- A custom VPC with public and private subnets across three Availability Zones
- NAT Gateway for private subnet outbound internet access
- An EKS managed node group running on private subnets
- AWS WAFv2 Web ACL protecting the internet-facing load balancer
- CloudWatch log groups for EKS control plane and application logs
- A complete observability stack: Prometheus, Alertmanager, Grafana, Loki, and Promtail
- An AWS Load Balancer Controller to manage ALBs/NLBs from Kubernetes
- All persistent storage backed by encrypted gp3 EBS volumes
- Remote Terraform state stored in a versioned, encrypted S3 bucket

**Cloud Provider:** AWS
**Region:** us-east-1
**Kubernetes Version:** 1.31
**Terraform Version:** >= 1.5.0

---

## 2. Repository Structure

```
.
├── backend/                   # Step 1: Bootstrap S3 remote state bucket (independent root module)
│   ├── main.tf                # S3 bucket + versioning + encryption
│   ├── provider.tf            # AWS + random providers, local backend
│   ├── variables.tf           # region variable
│   ├── outputs.tf             # Outputs bucket name
│   └── backend.tf.reference   # Reference snippet for root provider.tf
│
├── modules/
│   ├── networking/            # VPC, subnets, IGW, NAT Gateway, route tables
│   ├── security_groups/       # Cluster SG, nodes SG, SG rules
│   ├── iam/                   # EKS cluster role + node group role + policy attachments
│   ├── eks/                   # EKS cluster, node group, pre-destroy cleanup
│   ├── waf/                   # WAFv2 Web ACL with managed rules + rate limiting
│   └── cloudwatch/            # CloudWatch log groups for EKS and application logs
│
├── monitoring/                # Step 3: Helm-based observability stack (independent root module)
│   ├── main.tf                # gp3 StorageClass, LB Controller, Prometheus, Loki
│   ├── provider.tf            # AWS, Helm, Kubernetes providers
│   ├── versions.tf            # Provider version constraints
│   ├── variables.tf           # cluster_name, region, grafana_admin_password
│   └── outputs.tf             # Grafana URL command
│
├── main.tf                    # Calls all six modules
├── provider.tf                # AWS provider + optional S3 backend
├── variables.tf               # Input variable declarations
├── terraform.tfvars           # Variable values
└── output.tf                  # Cluster name, endpoint, VPC ID, WAF ARN, log group names
```

---

## 3. Architecture

```
                    Internet
                       │
               ┌───────▼────────┐
               │  AWS WAFv2     │
               │  CommonRules   │
               │  KnownBadInput │
               │  Rate Limit    │
               └───────┬────────┘
                       │
               ┌───────▼────────┐
               │ Internet GW    │
               └───────┬────────┘
                       │
   ┌───────────────────┼──────────────────────┐
   │  VPC  10.1.0.0/16                        │
   │                                          │
   │  Public Subnets (AZ1–AZ3)               │
   │    NAT Gateway + Elastic IP              │
   │    AWS Load Balancer (Grafana) ◄─── WAF  │
   │                                          │
   │  Private Subnets (AZ1–AZ3)              │
   │    EKS Worker Nodes (t3.medium)          │
   │                                          │
   │    Namespace: monitoring                 │
   │      Prometheus · Alertmanager · Grafana │
   │      Loki · Promtail                     │
   │                                          │
   │  EKS Control Plane (AWS Managed)         │
   │    Logs → CloudWatch                     │
   └──────────────────────────────────────────┘

   CloudWatch Log Groups
     /aws/eks/my-eks-cluster/cluster      (30 days)
     /aws/eks/my-eks-cluster/application  (30 days)

   S3 Bucket — Terraform Remote State (versioned, AES256)
```

---

## 4. Module: `backend/`

Bootstraps the S3 bucket used for Terraform remote state. Must be applied first — uses a local backend intentionally since the remote bucket doesn't exist yet.

| Resource | Description |
|---|---|
| `aws_s3_bucket` | State bucket with random hex suffix |
| `aws_s3_bucket_versioning` | Enables versioning for state history |
| `aws_s3_bucket_server_side_encryption_configuration` | AES256 encryption at rest |
| `aws_s3_bucket_public_access_block` | Blocks all public access |

---

## 5. Module: `networking/`

| Resource | Details |
|---|---|
| `aws_vpc` | CIDR `10.1.0.0/16`, DNS support and hostnames enabled |
| `aws_subnet.public` (×3) | `10.1.1–3.0/24` across AZ1–AZ3, tagged `kubernetes.io/role/elb=1` |
| `aws_subnet.private` (×3) | `10.1.11–13.0/24` across AZ1–AZ3, tagged `kubernetes.io/role/internal-elb=1` |
| `aws_internet_gateway` | Attached to VPC |
| `aws_eip.nat` | Elastic IP for NAT Gateway |
| `aws_nat_gateway` | In public subnet AZ1; private subnets route outbound through this |
| `aws_route_table.public` | `0.0.0.0/0` → Internet Gateway |
| `aws_route_table.private` | `0.0.0.0/0` → NAT Gateway |

---

## 6. Module: `security_groups/`

| Security Group | Inbound Rules |
|---|---|
| `eks_cluster` (control plane) | Port 443 from worker nodes; port 443 from `var.admin_cidr` |
| `eks_nodes` (worker nodes) | All traffic from other nodes; all TCP from control plane |

Both groups allow all outbound traffic.

> **Action required:** Set `admin_cidr` in `modules/security_groups/variables.tf` to your actual IP.

---

## 7. Module: `iam/`

| Role | Trust Principal | Policies |
|---|---|---|
| `eks-cluster-role` | `eks.amazonaws.com` | `AmazonEKSClusterPolicy`, `AmazonEKSServicePolicy` |
| `nodegroup-role` | `ec2.amazonaws.com` | `AmazonEKSWorkerNodePolicy`, `AmazonEKS_CNI_Policy`, `AmazonEC2ContainerRegistryReadOnly` |

---

## 8. Module: `eks/`

| Setting | Value |
|---|---|
| Kubernetes version | `1.31` (via `var.kubernetes_version`) |
| Subnets | All public + private subnets |
| Private endpoint | Enabled |
| Public endpoint | Enabled (restrict `public_access_cidrs` for production) |
| Control plane logs | `api`, `audit`, `authenticator`, `controllerManager`, `scheduler` → CloudWatch |
| Node instance type | `t3.medium` |
| Node subnets | Private only (outbound via NAT Gateway) |
| Scaling | desired=2, min=2, max=4, max_unavailable=1 |

### Pre-destroy Cleanup

`null_resource.k8s_cleanup` runs on `terraform destroy` to delete all Kubernetes `LoadBalancer` services, allowing AWS to clean up ELBs/ENIs/SGs before VPC deletion.

---

## 9. Module: `waf/`

Creates an AWS WAFv2 Web ACL (REGIONAL scope) and optionally associates it with an ALB.

| Rule | Priority | Action |
|---|---|---|
| `AWSManagedRulesCommonRuleSet` | 1 | Allow (managed — blocks SQLi, XSS, etc.) |
| `AWSManagedRulesKnownBadInputsRuleSet` | 2 | Allow (managed — blocks known malicious inputs) |
| `RateLimitRule` | 3 | Block IPs exceeding `var.rate_limit` requests per 5 min (default: 2000) |

All rules emit CloudWatch metrics and sampled requests for visibility.

To associate with the Grafana ALB after provisioning:

```hcl
module "waf" {
  source  = "./modules/waf"
  name    = var.cluster_name
  alb_arn = "<grafana-alb-arn>"
  tags    = var.tags
}
```

---

## 10. Module: `cloudwatch/`

Creates CloudWatch log groups for EKS log ingestion.

| Log Group | Retention | Purpose |
|---|---|---|
| `/aws/eks/<cluster>/cluster` | 30 days | EKS control plane logs (api, audit, authenticator, etc.) |
| `/aws/eks/<cluster>/application` | 30 days | Application-level logs from workloads |

Retention is configurable via `var.retention_days` (default: `30`).

---

## 11. Module: `monitoring/`

Independent Terraform root module. Reads EKS cluster credentials from AWS data sources — no manual kubeconfig needed.

### gp3 StorageClass

Default StorageClass using `ebs.csi.aws.com`, encrypted, `WaitForFirstConsumer` binding.

### AWS Load Balancer Controller

Helm chart `aws-load-balancer-controller` v1.7.2 in `kube-system`.

> Requires IRSA configuration — see [Known Issues](#15-known-issues--todos).

### kube-prometheus-stack

Helm chart `prometheus-community/kube-prometheus-stack` v58.2.2, namespace `monitoring`.

| Component | Storage |
|---|---|
| Prometheus | 20 Gi gp3 |
| Alertmanager | 5 Gi gp3 |
| Grafana | 10 Gi gp3 — exposed via internet-facing ALB |

```bash
# Get Grafana URL
kubectl get svc -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
# Login: admin / var.grafana_admin_password
```

### Loki Stack

Helm chart `grafana/loki-stack` v2.10.2, namespace `monitoring`.

| Component | Storage |
|---|---|
| Loki | 20 Gi gp3 |
| Promtail | DaemonSet — ships node logs to Loki |

Add Loki as Grafana datasource: `http://loki:3100`

---

## 12. Variables Reference

### Root module

| Variable | Default | Description |
|---|---|---|
| `region` | `us-east-1` | AWS region |
| `cluster_name` | `my-eks-cluster` | EKS cluster name |
| `vpc_cidr` | `10.1.0.0/16` | VPC CIDR block |
| `public_subnet_cidrs` | `["10.1.1.0/24","10.1.2.0/24","10.1.3.0/24"]` | Public subnet CIDRs |
| `private_subnet_cidrs` | `["10.1.11.0/24","10.1.12.0/24","10.1.13.0/24"]` | Private subnet CIDRs |
| `kubernetes_version` | `1.31` | EKS Kubernetes version |
| `node_instance_type` | `t3.medium` | Worker node EC2 instance type |
| `desired_nodes` | `2` | Desired node count |
| `min_nodes` | `2` | Minimum node count |
| `max_nodes` | `4` | Maximum node count |
| `tags` | `{Environment, Project, Owner}` | Common resource tags |

### monitoring module

| Variable | Default | Description |
|---|---|---|
| `region` | `us-east-1` | AWS region |
| `cluster_name` | `my-eks-cluster` | EKS cluster to attach to |
| `grafana_admin_password` | `changeme123!` | Grafana admin password (sensitive) |

---

## 13. Deployment Guide

### Step 1 — Bootstrap Remote State

```bash
cd backend
terraform init
terraform apply
```

Copy the output bucket name into the `backend "s3"` block in `provider.tf`, then uncomment it.

### Step 2 — Provision EKS Cluster

```bash
cd ..
terraform init
terraform apply
```

Creates VPC, subnets, NAT Gateway, security groups, IAM roles, EKS cluster + node group, WAF Web ACL, and CloudWatch log groups. Takes ~15 minutes.

### Step 3 — Configure kubectl

```bash
aws eks update-kubeconfig --name my-eks-cluster --region us-east-1
kubectl get nodes
```

### Step 4 — Deploy Monitoring Stack

```bash
cd monitoring
terraform init
terraform apply
```

### Step 5 — Access Grafana

```bash
kubectl get svc -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

Login: `admin` / `changeme123!`

---

## 14. Teardown Guide

```bash
# 1. Remove monitoring stack first
cd monitoring && terraform destroy

# 2. Destroy EKS cluster, WAF, CloudWatch, VPC
cd .. && terraform destroy
```

> The `backend/` S3 bucket has `force_destroy = false`. Delete it manually from the AWS Console after confirming state is no longer needed.

---

## 15. Known Issues & TODOs

| # | Item | Status | Action |
|---|---|---|---|
| 1 | Admin CIDR | ⚠️ Placeholder `203.0.113.0/24` | Replace in `modules/security_groups/variables.tf` |
| 2 | EKS public endpoint | ⚠️ Open to `0.0.0.0/0` | Restrict `public_access_cidrs` in `modules/eks/main.tf` for production |
| 3 | IRSA for LB Controller | ⚠️ Not configured | Create IAM policy + OIDC provider + service account role |
| 4 | S3 backend | ⚠️ Commented out | Fill in bucket name in `provider.tf` after step 1 |
| 5 | Grafana password | ⚠️ Default value | Override `var.grafana_admin_password` before applying |
| 6 | WAF ALB association | ⚠️ Not yet linked | Pass Grafana ALB ARN to `module.waf.alb_arn` after first apply |
| 7 | EBS CSI Driver | ⚠️ Must be installed | Enable EBS CSI add-on before applying monitoring |
| 8 | Single NAT Gateway | ℹ️ AZ1 only | Add one NAT Gateway per AZ for high availability |
| 9 | NAT Gateway cost | ℹ️ ~$0.045/hr | Destroy when not in use for dev/test |
