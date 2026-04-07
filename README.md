# modify-eks-cluster

Terraform project that provisions a production-ready Amazon EKS cluster on AWS, including networking, IAM, security groups, and a full observability stack. Infrastructure is organized into reusable child modules.

## Architecture

```
Internet
   │
Internet Gateway
   │
┌──────────────────────────────────────────────┐
│  VPC  10.1.0.0/16                            │
│                                              │
│  Public Subnets (AZ1–AZ3)                   │
│    NAT Gateway + Elastic IP                  │
│    AWS Load Balancer (Grafana)               │
│                                              │
│  Private Subnets (AZ1–AZ3)                  │
│    EKS Worker Nodes (t3.medium)              │
│                                              │
│    Namespace: monitoring                     │
│      Prometheus · Alertmanager · Grafana     │
│      Loki · Promtail                         │
│                                              │
│  EKS Control Plane (AWS Managed)             │
└──────────────────────────────────────────────┘

S3 Bucket — Terraform Remote State
```

## Prerequisites

| Tool | Version |
|------|---------|
| Terraform | >= 1.5.0 |
| AWS CLI | configured with sufficient IAM permissions |
| kubectl | any recent version |
| helm | any recent version |

## Repository Structure

```
.
├── backend/                   # Step 1: S3 remote state bucket (independent root module)
│
├── modules/
│   ├── networking/            # VPC, subnets, IGW, NAT Gateway, route tables
│   ├── security_groups/       # Cluster SG, nodes SG, SG rules
│   ├── iam/                   # EKS cluster role + node group role + policy attachments
│   └── eks/                   # EKS cluster, node group, pre-destroy cleanup
│
├── monitoring/                # Step 3: Helm-based observability stack (independent root module)
│
├── main.tf                    # Calls all four modules
├── provider.tf                # AWS provider + optional S3 backend
├── variables.tf               # Input variable declarations
├── terraform.tfvars           # Variable values
└── output.tf                  # Cluster name, endpoint, VPC ID
```

> `s3-backend/` is an unused directory and can be ignored.

## Quick Start

### 1 — Bootstrap remote state

```bash
cd backend
terraform init
terraform apply
```

Copy the output bucket name into the `backend "s3"` block in `provider.tf`, then uncomment it.

### 2 — Provision the EKS cluster

```bash
cd ..
terraform init
terraform apply
```

Takes ~15 minutes. Creates VPC, subnets, NAT Gateway, security groups, IAM roles, and the EKS cluster + node group.

### 3 — Configure kubectl

```bash
aws eks update-kubeconfig --name my-eks-cluster --region us-east-1
kubectl get nodes
```

### 4 — Deploy the monitoring stack

```bash
cd monitoring
terraform init
terraform apply
```

Deploys Prometheus, Alertmanager, Grafana, Loki, and Promtail via Helm.

### 5 — Access Grafana

```bash
kubectl get svc -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

Login: `admin` / value of `var.grafana_admin_password`

## Key Variables (`terraform.tfvars`)

| Variable | Default | Description |
|----------|---------|-------------|
| `cluster_name` | `my-eks-cluster` | EKS cluster name |
| `region` | `us-east-1` | AWS region |
| `vpc_cidr` | `10.1.0.0/16` | VPC CIDR |
| `kubernetes_version` | `1.31` | EKS Kubernetes version |
| `node_instance_type` | `t3.medium` | Worker node instance type |
| `desired_nodes` | `2` | Desired node count |
| `min_nodes` | `2` | Minimum node count |
| `max_nodes` | `4` | Maximum node count |

## Modules

| Module | Description |
|--------|-------------|
| `modules/networking` | VPC, public/private subnets across 3 AZs, IGW, NAT Gateway, route tables |
| `modules/security_groups` | Control plane SG, worker nodes SG, and all ingress rules |
| `modules/iam` | EKS cluster IAM role + node group IAM role with required policy attachments |
| `modules/eks` | EKS cluster, managed node group, pre-destroy LoadBalancer cleanup |

## Teardown

```bash
# 1. Remove monitoring stack first
cd monitoring && terraform destroy

# 2. Destroy EKS cluster and VPC
cd .. && terraform destroy
```

> The `backend/` S3 bucket has `force_destroy = false`. Delete it manually from the AWS Console after confirming state is no longer needed.

## Known Issues

| # | Item | Action |
|---|------|--------|
| 1 | Admin CIDR | Replace `203.0.113.0/24` in `modules/security_groups/variables.tf` with your actual IP |
| 2 | Public endpoint | Restrict `public_access_cidrs` in `modules/eks/main.tf` for production |
| 3 | IRSA for LB Controller | Configure IAM policy + OIDC provider + service account role |
| 4 | S3 backend | Uncomment and fill in bucket name in `provider.tf` after step 1 |
| 5 | EBS CSI Driver | Enable the EBS CSI add-on on the cluster before applying monitoring |
