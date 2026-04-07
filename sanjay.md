# EKS Cluster Project

A Terraform project that provisions a production-ready Amazon EKS cluster on AWS, along with a full monitoring stack (Prometheus, Loki, Grafana) and an AWS Load Balancer Controller.

> Architecture diagram: open `architecture.drawio` in [draw.io](https://app.diagrams.net) (File → Open from → Device)

---

## Architecture Overview

```
Internet
    │
    ▼
Internet Gateway
    │
    ├──────────────────────────────────────┐
    ▼                                      ▼
Public Subnet AZ1                  Public Subnet AZ2
(10.1.1.0/24)                      (10.1.2.0/24)
┌─────────────┐                    ┌──────────────────┐
│ NAT Gateway │                    │ AWS Load Balancer │
│ + Elastic IP│                    │ (Grafana)        │
└──────┬──────┘                    └────────┬─────────┘
       │ outbound                           │
       ▼                                    ▼
Private Subnet AZ1                 Private Subnet AZ2
(10.1.11.0/24)                     (10.1.12.0/24)
┌──────────────────────────────────────────────────────┐
│                  EKS Node Group                      │
│  Worker Node (t3.small)    Worker Node (t3.small)    │
│                                                      │
│  Pods (monitoring namespace):                        │
│  ┌───────────┐ ┌────────────┐ ┌────────┐ ┌──────┐  │
│  │ Prometheus│ │Alertmanager│ │Grafana │ │ Loki │  │
│  │  20Gi gp3 │ │  5Gi gp3  │ │10Gi gp3│ │20Gi  │  │
│  └───────────┘ └────────────┘ └────────┘ │ gp3  │  │
│                                           └──────┘  │
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │ Promtail DaemonSet│  │ LB Controller (kube-sys) │ │
│  └──────────────────┘  └──────────────────────────┘ │
└──────────────────────────────────────────────────────┘
       │
       ▼
EKS Control Plane (AWS Managed)
       │
       ├── IAM Role: eks-cluster-role
       └── IAM Role: nodegroup-role

S3 Bucket (Terraform Remote State)
  - Versioning enabled
  - AES256 encryption
  - Public access blocked
```

---

## Project Structure

```
eks-cluster/
├── backend/              # Bootstraps S3 remote state backend
├── monitoring/           # Monitoring stack (LB Controller, Prometheus, Loki, Grafana)
├── architecture.drawio   # Architecture diagram (open in draw.io)
├── main.tf               # Core infrastructure (VPC, EKS, IAM, Security Groups)
├── provider.tf           # AWS provider + Terraform version constraints
├── variables.tf          # Input variable declarations
├── terraform.tfvars      # Variable values (region, cluster config, tags)
├── output.tf             # (reserved for outputs)
└── ec2.tf                # (reserved for standalone EC2 resources)
```

---

## Modules Overview

### 1. `backend/` — Remote State Bootstrap

Creates the S3 bucket used to store Terraform state remotely before provisioning the cluster.

**Resources created:**
- `aws_s3_bucket` — uniquely named with a random suffix
- S3 versioning enabled
- AES256 server-side encryption
- Public access fully blocked

```bash
cd backend
terraform init
terraform apply
# Copy the output bucket name into provider.tf backend block
```

> Uses a local backend intentionally — it bootstraps the remote backend, so it cannot use it itself.

---

### 2. Root — Core EKS Infrastructure (`main.tf`)

#### Networking (VPC)

| Resource | Details |
|---|---|
| VPC | CIDR `10.1.0.0/16`, DNS support enabled |
| Public Subnets | 2 subnets across 2 AZs, tagged for internet-facing ELBs |
| Private Subnets | 2 subnets across 2 AZs, tagged for internal ELBs |
| Internet Gateway | Attached to VPC for public internet access |
| NAT Gateway | In public subnet AZ1, with Elastic IP — private nodes route outbound traffic through this |
| Route Tables | Public → IGW, Private → NAT Gateway |

#### Security Groups

| Security Group | Purpose |
|---|---|
| `eks_cluster` | EKS control plane (API server) |
| `eks_nodes` | Worker nodes |

Key rules:
- Nodes → Cluster: port 443
- Node ↔ Node: all traffic
- Cluster → Nodes: all TCP
- Admin → Cluster API: port 443 from `203.0.113.0/24` (**change this to your IP**)

#### IAM Roles

| Role | Policies Attached |
|---|---|
| `eks_cluster` role | `AmazonEKSClusterPolicy`, `AmazonEKSServicePolicy` |
| `eks_node_group` role | `AmazonEKSWorkerNodePolicy`, `AmazonEKS_CNI_Policy`, `AmazonEC2ContainerRegistryReadOnly` |

#### EKS Cluster & Node Group

- Kubernetes control plane managed by AWS
- Public + private endpoint access enabled
- Managed node group: `t3.small`, placed in **private subnets** (outbound via NAT)
- Auto-scaling: min 2, desired 2, max 4

#### Pre-destroy Cleanup

A `null_resource.k8s_cleanup` runs on `terraform destroy` to delete all `LoadBalancer` services and wait 30s for ELBs/ENIs to deregister — prevents VPC deletion failures.

---

### 3. `monitoring/` — Observability Stack

Separate Terraform root module. Reads cluster details from AWS and configures Helm/Kubernetes providers automatically.

#### gp3 StorageClass

Set as the cluster default. All monitoring components use gp3 EBS:

| Component | Storage |
|---|---|
| Prometheus | 20 Gi |
| Grafana | 10 Gi |
| Alertmanager | 5 Gi |
| Loki | 20 Gi |

#### AWS Load Balancer Controller

Deployed via Helm into `kube-system`. Enables `Service`/`Ingress` resources to provision AWS ALBs/NLBs.

#### kube-prometheus-stack

Deploys Prometheus + Grafana + Alertmanager via `prometheus-community/kube-prometheus-stack`.

- Grafana exposed via internet-facing AWS Load Balancer

```bash
# Get Grafana URL
kubectl get svc -n monitoring kube-prometheus-stack-grafana \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Credentials
Username: admin
Password: changeme123!   # override via var.grafana_admin_password
```

#### Loki Stack

Deploys Loki + Promtail via `grafana/loki-stack`.

- Promtail DaemonSet ships logs from every node to Loki
- Add Loki as Grafana datasource: `http://loki:3100`

---

## Configuration (`terraform.tfvars`)

```hcl
region       = "us-east-1"
cluster_name = "my-eks-cluster"

vpc_cidr             = "10.1.0.0/16"
public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnet_cidrs = ["10.1.11.0/24", "10.1.12.0/24"]

node_instance_type = "t3.small"
desired_nodes      = 2
min_nodes          = 2
max_nodes          = 4

tags = {
  Environment = "dev"
  Project     = "eks-demo"
  Owner       = "infrastructure"
}
```

---

## Deployment Order

```bash
# 1. Bootstrap remote state
cd backend && terraform init && terraform apply

# 2. (Optional) Uncomment S3 backend block in provider.tf

# 3. Provision VPC + EKS cluster
cd .. && terraform init && terraform apply

# 4. Configure kubectl
aws eks update-kubeconfig --name my-eks-cluster --region us-east-1

# 5. Deploy monitoring stack
cd monitoring && terraform init && terraform apply
```

---

## Teardown

```bash
cd monitoring && terraform destroy
cd .. && terraform destroy
```

---

## Known Limitations & TODOs

| Item | Status |
|---|---|
| NAT Gateway | ✅ Active — private nodes route outbound via NAT |
| Admin CIDR (`203.0.113.0/24`) | ⚠️ Placeholder — replace with your actual IP in `main.tf` |
| EKS public access | ⚠️ Open to `0.0.0.0/0` — restrict for production |
| IRSA for LB Controller | ⚠️ Not configured — required for Load Balancer Controller to function |
| S3 backend | ⚠️ Commented out in `provider.tf` — fill in after running `backend/` |
| Grafana password | ⚠️ Default `changeme123!` — override via `var.grafana_admin_password` |
| NAT Gateway cost | ℹ️ ~$0.045/hr + data transfer — destroy when not in use for dev |
