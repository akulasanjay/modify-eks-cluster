# GitHub Actions CI/CD — EKS Cluster Deployment

## Overview

The workflow at `.github/workflows/deploy.yml` automates the full lifecycle of the EKS cluster:
bootstrap remote state → provision infrastructure → deploy monitoring stack.

```
push/PR to main
       │
       ▼
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  bootstrap  │────►│   terraform     │────►│   monitoring     │
│  S3 bucket  │     │  plan/apply/    │     │  Prometheus      │
│  (backend/) │     │  destroy        │     │  Grafana · Loki  │
└─────────────┘     └─────────────────┘     └──────────────────┘
```

---

## Triggers

| Event | Behaviour |
|---|---|
| `push` to `main` | Full deploy: bootstrap → apply → monitoring |
| `pull_request` to `main` | Plan only — posts diff as PR comment |
| `workflow_dispatch` | Manual run — choose `plan`, `apply`, or `destroy` |

---

## Prerequisites

### 1. AWS OIDC Provider (one-time setup)

GitHub Actions authenticates to AWS via OIDC — no long-lived keys stored in secrets.

```bash
# Create the OIDC provider in your AWS account
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. IAM Role for GitHub Actions

Create an IAM role with a trust policy scoped to your repository:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<YOUR_ORG>/<YOUR_REPO>:*"
        },
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

Attach the following AWS managed policies to the role:

| Policy | Purpose |
|---|---|
| `AmazonEKSClusterPolicy` | Manage EKS clusters |
| `AmazonEC2FullAccess` | VPC, subnets, NAT, security groups |
| `IAMFullAccess` | Create EKS IAM roles |
| `AmazonS3FullAccess` | Terraform remote state bucket |
| `CloudWatchLogsFullAccess` | Create log groups |
| `WAFV2FullAccess` | WAF Web ACL |

> For tighter security, replace these with a custom least-privilege policy scoped to your resource names.

---

## Repository Configuration

### Secrets

Go to **Settings → Secrets and variables → Actions → Secrets** and add:

| Secret | Description |
|---|---|
| `AWS_ROLE_ARN` | ARN of the IAM role created above, e.g. `arn:aws:iam::123456789012:role/github-eks-deploy` |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin password (min 8 chars) |
| `TF_STATE_BUCKET` | S3 bucket name fallback — used if bootstrap job was already run previously |

### Variables

Go to **Settings → Secrets and variables → Actions → Variables** and add:

| Variable | Default | Description |
|---|---|---|
| `CLUSTER_NAME` | `my-eks-cluster` | EKS cluster name passed to Terraform |

### Environment Protection (optional but recommended)

The `apply` and `destroy` actions target the `production` environment. To require manual approval before they run:

1. Go to **Settings → Environments → New environment** → name it `production`
2. Enable **Required reviewers** and add yourself
3. Apply and destroy jobs will pause and wait for approval

---

## Workflow Jobs

### Job 1: `bootstrap`

Runs `terraform apply` inside `backend/` to create the S3 state bucket.

- Skipped on `pull_request` (plan-only runs don't need a real bucket)
- Outputs the bucket name to subsequent jobs
- Safe to re-run — S3 bucket creation is idempotent

### Job 2: `terraform`

| Step | Description |
|---|---|
| Inject backend | Uncomments and fills the `backend "s3"` block in `provider.tf` with the bucket name |
| `terraform init` | Initialises providers and S3 backend |
| `terraform validate` | Syntax and config validation |
| `terraform plan` | Generates execution plan, saved as `tfplan` |
| Post PR comment | On pull requests, posts the plan output as a comment |
| `terraform apply` | Applies `tfplan` on push to main or manual apply |
| `terraform destroy` | Full teardown on manual destroy trigger |
| Configure kubectl | Runs `aws eks update-kubeconfig` and `kubectl get nodes` to verify |

### Job 3: `monitoring`

Runs after `terraform` succeeds. Deploys the observability stack into the cluster.

| Step | Description |
|---|---|
| `terraform init/apply` | Deploys Prometheus, Alertmanager, Grafana, Loki, Promtail via Helm |
| Get Grafana URL | Prints the ALB hostname for Grafana access |

---

## Usage

### Deploy (automatic)

```bash
git add .
git commit -m "deploy eks cluster"
git push origin main
# Workflow triggers automatically
```

### Manual plan

Go to **Actions → Deploy EKS Cluster → Run workflow** → select `plan`

### Manual apply

Go to **Actions → Deploy EKS Cluster → Run workflow** → select `apply`

### Destroy

Go to **Actions → Deploy EKS Cluster → Run workflow** → select `destroy`

> Destroy runs monitoring teardown first (`cd monitoring && terraform destroy`), then the root module.

---

## Monitoring the Run

1. Go to **Actions** tab in your repository
2. Click the running workflow
3. Expand each job to see live logs
4. On PRs, check the PR comments for the Terraform plan diff

---

## Secrets Reference Summary

```
GitHub Repository
├── Secrets
│   ├── AWS_ROLE_ARN              ← arn:aws:iam::<id>:role/<name>
│   ├── GRAFANA_ADMIN_PASSWORD    ← your-secure-password
│   └── TF_STATE_BUCKET           ← my-eks-tfstate-<random>
└── Variables
    └── CLUSTER_NAME              ← my-eks-cluster
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` | OIDC provider not created or trust policy wrong | Re-check the trust policy `sub` condition matches your repo |
| `No cluster found for name: my-eks-cluster` | Apply hasn't completed yet | Wait for the `terraform` job to finish before `monitoring` runs |
| `backend "s3" not configured` | Bucket name not injected | Ensure `TF_STATE_BUCKET` secret is set or bootstrap job ran |
| `Error: Kubernetes cluster unreachable` | kubeconfig not configured in monitoring job | Check the `configure kubectl` step ran successfully in the terraform job |
| Monitoring apply fails with PVC errors | EBS CSI driver not installed | Add the EBS CSI add-on to the EKS cluster before applying monitoring |
