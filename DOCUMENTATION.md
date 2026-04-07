# EKS Cluster Project — Technical Documentation

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Architecture](#3-architecture)
4. [Module: backend](#4-module-backend)
5. [Module: Root — EKS Infrastructure](#5-module-root--eks-infrastructure)
6. [Module: monitoring](#6-module-monitoring)
7. [Variables Reference](#7-variables-reference)
8. [Deployment Guide](#8-deployment-guide)
9. [Teardown Guide](#9-teardown-guide)
10. [Known Issues & TODOs](#10-known-issues--todos)

---

## 1. Project Overview

This project provisions a fully functional Amazon EKS cluster on AWS using Terraform, including:

- A custom VPC with public and private subnets across two Availability Zones
- NAT Gateway for private subnet outbound internet access
- An EKS managed node group running on private subnets
- A complete observability stack: Prometheus, Alertmanager, Grafana, Loki, and Promtail
- An AWS Load Balancer Controller to manage ALBs/NLBs from Kubernetes
- All persistent storage backed by encrypted gp3 EBS volumes
- Remote Terraform state stored in a versioned, encrypted S3 bucket

**Cloud Provider:** AWS
**Region:** us-east-1
**Terraform Version:** >= 1.5.0

---

## 2. Repository Structure

```
eks-cluster/
├── backend/                  # Step 1: Bootstrap S3 remote state bucket
│   ├── main.tf               # S3 bucket + versioning + encryption
│   ├── provider.tf           # AWS + random providers, local backend
│   ├── variables.tf          # region variable
│   ├── outputs.tf            # Outputs bucket name
│   └── backend.tf.reference  # Reference snippet for root provider.tf
│
├── monitoring/               # Step 3: Observability stack (Helm-based)
│   ├── main.tf               # gp3 StorageClass, LB Controller, Prometheus, Loki
│   ├── provider.tf           # AWS, Helm, Kubernetes providers
│   ├── versions.tf           # Provider version constraints
│   ├── variables.tf          # cluster_name, region, grafana_admin_password
│   └── outputs.tf            # Grafana URL command
│
├── main.tf                   # Step 2: VPC, subnets, IGW, NAT, SGs, IAM, EKS
├── provider.tf               # AWS provider, Terraform version, S3 backend (optional)
├── variables.tf              # All input variable declarations
├── terraform.tfvars          # Actual variable values
├── output.tf                 # (reserved)
├── ec2.tf                    # (reserved)
├── architecture.drawio       # Architecture diagram (open in draw.io)
└── README.md                 # Quick-start guide
```

---

## 3. Architecture

Open `architecture.drawio` at [app.diagrams.net](https://app.diagrams.net) for the visual diagram.

```
                          ┌─────────────┐
                          │   Internet  │
                          └──────┬──────┘
                                 │
                          ┌──────▼──────┐
                          │Internet GW  │
                          └──────┬──────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                                     │
   ┌──────────▼──────────┐           ┌──────────────▼──────────┐
   │  Public Subnet AZ1  │           │   Public Subnet AZ2     │
   │   10.1.1.0/24       │           │   10.1.2.0/24           │
   │  ┌───────────────┐  │           │  ┌────────────────────┐ │
   │  │ NAT Gateway   │  │           │  │  AWS Load Balancer │ │
   │  │ + Elastic IP  │  │           │  │  (Grafana)         │ │
   │  └───────┬───────┘  │           │  └─────────┬──────────┘ │
   └──────────┼──────────┘           └────────────┼────────────┘
              │ outbound                           │
              ▼                                    ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                    Private Subnets (AZ1 + AZ2)              │
   │                10.1.11.0/24  |  10.1.12.0/24                │
   │                                                              │
   │   Worker Node (t3.small)        Worker Node (t3.small)      │
   │                                                              │
   │   Namespace: monitoring                                      │
   │   ┌───────────┐ ┌────────────┐ ┌─────────┐ ┌────────────┐  │
   │   │Prometheus │ │Alertmanager│ │ Grafana │ │    Loki    │  │
   │   │ 20Gi gp3  │ │  5Gi gp3  │ │10Gi gp3 │ │ 20Gi gp3  │  │
   │   └───────────┘ └────────────┘ └────┬────┘ └─────┬──────┘  │
   │                                     │             │         │
   │   ┌──────────────────┐    datasources: Prometheus + Loki    │
   │   │ Promtail DaemonSet│──ships logs──────────────►│         │
   │   └──────────────────┘                                      │
   │   ┌──────────────────────────┐                              │
   │   │ LB Controller (kube-sys) │                              │
   │   └──────────────────────────┘                              │
   └──────────────────────────────────────────────────────────────┘
              │
   ┌──────────▼──────────────────────────────────────────────────┐
   │  EKS Control Plane (AWS Managed)                            │
   │  IAM: eks-cluster-role  |  nodegroup-role                   │
   └─────────────────────────────────────────────────────────────┘

   S3 Bucket — Terraform Remote State (versioned, AES256 encrypted)
```

---

## 4. Module: `backend/`

Bootstraps the S3 bucket used for Terraform remote state. Must be applied first, before the root module.

### Resources

| Resource | Description |
|---|---|
| `aws_s3_bucket` | State bucket with random hex suffix for uniqueness |
| `aws_s3_bucket_versioning` | Enables versioning for state history and rollback |
| `aws_s3_bucket_server_side_encryption_configuration` | AES256 encryption at rest |
| `aws_s3_bucket_public_access_block` | Blocks all public access |

### Notes

- Uses a **local backend** intentionally — it cannot use the remote backend it is creating
- `force_destroy = false` prevents accidental deletion of state history
- After applying, copy the output bucket name into the `backend "s3"` block in the root `provider.tf`

---

## 5. Module: Root — EKS Infrastructure

### 5.1 Networking

| Resource | Details |
|---|---|
| `aws_vpc` | CIDR `10.1.0.0/16`, DNS support and hostnames enabled |
| `aws_subnet.public` (×2) | `10.1.1.0/24`, `10.1.2.0/24` — tagged `kubernetes.io/role/elb=1` |
| `aws_subnet.private` (×2) | `10.1.11.0/24`, `10.1.12.0/24` — tagged `kubernetes.io/role/internal-elb=1` |
| `aws_internet_gateway` | Attached to VPC; public subnets route through this |
| `aws_eip.nat` | Elastic IP allocated for the NAT Gateway |
| `aws_nat_gateway` | Placed in public subnet AZ1; private subnets route outbound traffic through this |
| `aws_route_table.public` | Routes `0.0.0.0/0` → Internet Gateway |
| `aws_route_table.private` | Routes `0.0.0.0/0` → NAT Gateway |

### 5.2 Security Groups

| Security Group | Inbound Rules |
|---|---|
| `eks_cluster` (control plane) | Port 443 from worker nodes; port 443 from admin CIDR `203.0.113.0/24` |
| `eks_nodes` (worker nodes) | All traffic from other nodes; all TCP from control plane |

Both security groups allow all outbound traffic.

> **Action required:** Replace `203.0.113.0/24` in `main.tf` with your actual admin IP.

### 5.3 IAM

| Role | Trust | Policies |
|---|---|---|
| `eks-cluster-role` | `eks.amazonaws.com` | `AmazonEKSClusterPolicy`, `AmazonEKSServicePolicy` |
| `nodegroup-role` | `ec2.amazonaws.com` | `AmazonEKSWorkerNodePolicy`, `AmazonEKS_CNI_Policy`, `AmazonEC2ContainerRegistryReadOnly` |

### 5.4 EKS Cluster

| Setting | Value |
|---|---|
| Name | `my-eks-cluster` |
| Subnets | All public + private subnets |
| Private endpoint | Enabled |
| Public endpoint | Enabled (open to `0.0.0.0/0` — tighten for production) |

### 5.5 EKS Node Group

| Setting | Value |
|---|---|
| Instance type | `t3.small` |
| Subnets | Private subnets only (outbound via NAT Gateway) |
| Desired / Min / Max | 2 / 2 / 4 |
| Max unavailable during update | 1 |

### 5.6 Pre-destroy Cleanup (`null_resource.k8s_cleanup`)

Runs automatically on `terraform destroy`. It:

1. Updates kubeconfig for the cluster
2. Deletes all Kubernetes `LoadBalancer` services (which create AWS ELBs outside Terraform's control)
3. Waits 30 seconds for ELBs, ENIs, and security groups to fully deregister

This prevents VPC deletion from failing due to orphaned AWS resources.

---

## 6. Module: `monitoring/`

A separate Terraform root module. Reads the existing EKS cluster endpoint and credentials from AWS data sources and configures the Helm and Kubernetes providers automatically — no manual kubeconfig needed.

### 6.1 gp3 StorageClass

Creates a `gp3` EBS StorageClass and sets it as the cluster default. All monitoring components use this for persistent storage.

| Setting | Value |
|---|---|
| Provisioner | `ebs.csi.aws.com` |
| Volume binding | `WaitForFirstConsumer` |
| Reclaim policy | `Delete` |
| Encryption | Enabled |
| Volume expansion | Allowed |

### 6.2 AWS Load Balancer Controller

Deployed via Helm into `kube-system` (chart version `1.7.2`).

Enables Kubernetes `Service` (type `LoadBalancer`) and `Ingress` resources to automatically provision AWS ALBs and NLBs.

> **Note:** Requires an IAM role with the AWS Load Balancer Controller policy attached via IRSA (IAM Roles for Service Accounts). This is not yet configured in the project — see [Known Issues](#10-known-issues--todos).

### 6.3 kube-prometheus-stack

Helm chart: `prometheus-community/kube-prometheus-stack` version `58.2.2`
Namespace: `monitoring`

| Component | Description | Storage |
|---|---|---|
| Prometheus | Scrapes metrics from all nodes, pods, and Kubernetes components | 20 Gi gp3 |
| Alertmanager | Handles alert routing, grouping, and deduplication | 5 Gi gp3 |
| Grafana | Visualization dashboards; exposed via internet-facing AWS Load Balancer | 10 Gi gp3 |

Grafana access:

```bash
# Get the Load Balancer hostname
kubectl get svc -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Default login
Username: admin
Password: changeme123!   # set via var.grafana_admin_password
```

### 6.4 Loki Stack

Helm chart: `grafana/loki-stack` version `2.10.2`
Namespace: `monitoring`

| Component | Description | Storage |
|---|---|---|
| Loki | Log aggregation backend | 20 Gi gp3 |
| Promtail | DaemonSet that ships logs from every node to Loki | — |

Grafana is disabled in this chart (already running from kube-prometheus-stack).

To add Loki as a Grafana datasource:
- URL: `http://loki:3100`

---

## 7. Variables Reference

### Root module (`terraform.tfvars`)

| Variable | Default | Description |
|---|---|---|
| `region` | `us-east-1` | AWS region |
| `cluster_name` | `my-eks-cluster` | EKS cluster name |
| `vpc_cidr` | `10.1.0.0/16` | VPC CIDR block |
| `public_subnet_cidrs` | `["10.1.1.0/24", "10.1.2.0/24"]` | Public subnet CIDRs |
| `private_subnet_cidrs` | `["10.1.11.0/24", "10.1.12.0/24"]` | Private subnet CIDRs |
| `node_instance_type` | `t3.small` | EC2 instance type for worker nodes |
| `desired_nodes` | `2` | Desired node count |
| `min_nodes` | `2` | Minimum node count |
| `max_nodes` | `4` | Maximum node count |
| `tags` | `{Environment, Project, Owner}` | Common tags applied to all resources |

### monitoring module

| Variable | Default | Description |
|---|---|---|
| `region` | `us-east-1` | AWS region |
| `cluster_name` | `my-eks-cluster` | EKS cluster name to attach to |
| `grafana_admin_password` | `changeme123!` | Grafana admin password (sensitive) |

---

## 8. Deployment Guide

### Prerequisites

- AWS CLI configured with sufficient permissions
- Terraform >= 1.5.0
- `kubectl` installed
- `helm` installed (optional — Terraform manages Helm)

### Step 1 — Bootstrap Remote State

```bash
cd backend
terraform init
terraform apply
```

Copy the output bucket name. Then in the root `provider.tf`, uncomment and fill in the `backend "s3"` block:

```hcl
backend "s3" {
  bucket       = "<your-bucket-name>"
  key          = "eks-cluster/terraform.tfstate"
  region       = "us-east-1"
  use_lockfile = true
  encrypt      = true
}
```

### Step 2 — Provision EKS Cluster

```bash
cd ..
terraform init
terraform apply
```

This creates the VPC, subnets, NAT Gateway, security groups, IAM roles, and the EKS cluster + node group. Takes ~15 minutes.

### Step 3 — Configure kubectl

```bash
aws eks update-kubeconfig --name my-eks-cluster --region us-east-1
kubectl get nodes   # verify nodes are Ready
```

### Step 4 — Deploy Monitoring Stack

```bash
cd monitoring
terraform init
terraform apply
```

This deploys the gp3 StorageClass, AWS Load Balancer Controller, Prometheus, Alertmanager, Grafana, Loki, and Promtail. Takes ~5 minutes.

### Step 5 — Access Grafana

```bash
kubectl get svc -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

Open the URL in a browser. Login: `admin` / `changeme123!`

---

## 9. Teardown Guide

Destroy in reverse order to avoid dependency errors:

```bash
# 1. Remove monitoring stack first (deletes Helm releases, PVCs, EBS volumes)
cd monitoring
terraform destroy

# 2. Destroy the EKS cluster and VPC
# The k8s_cleanup provisioner auto-deletes LoadBalancer services before VPC removal
cd ..
terraform destroy
```

> The `backend/` S3 bucket has `force_destroy = false`. Delete it manually from the AWS Console after confirming state is no longer needed.

---

## 10. Known Issues & TODOs

| # | Item | Status | Action |
|---|---|---|---|
| 1 | Admin CIDR | ⚠️ Placeholder `203.0.113.0/24` | Replace with your actual IP in `main.tf` |
| 2 | EKS public endpoint | ⚠️ Open to `0.0.0.0/0` | Restrict `public_access_cidrs` for production |
| 3 | IRSA for LB Controller | ⚠️ Not configured | Create IAM policy + OIDC provider + service account role for the LB Controller to provision ELBs |
| 4 | S3 backend | ⚠️ Commented out | Fill in bucket name in `provider.tf` after running `backend/` |
| 5 | Grafana password | ⚠️ Default value | Override via `var.grafana_admin_password` before applying |
| 6 | NAT Gateway cost | ℹ️ ~$0.045/hr + data transfer | Destroy when not in use for dev/test environments |
| 7 | Single NAT Gateway | ℹ️ Only in AZ1 | For high availability, add a NAT Gateway per AZ |
| 8 | EBS CSI Driver | ⚠️ Must be installed | The gp3 StorageClass requires the EBS CSI driver add-on enabled on the cluster |
