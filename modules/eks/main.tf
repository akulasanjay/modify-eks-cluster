resource "aws_eks_cluster" "this" {
  name     = var.cluster_name
  role_arn = var.cluster_role_arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = concat(var.public_subnet_ids, var.private_subnet_ids)
    security_group_ids      = [var.cluster_sg_id]
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"] # Tighten for production
  }

  depends_on = [var.iam_cluster_policy_arns]

  tags = var.tags
}

resource "aws_eks_node_group" "this" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${var.cluster_name}-ng"
  node_role_arn   = var.node_role_arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = [var.node_instance_type]

  scaling_config {
    desired_size = var.desired_nodes
    min_size     = var.min_nodes
    max_size     = var.max_nodes
  }

  update_config {
    max_unavailable = 1
  }

  depends_on = [var.iam_node_policy_arns]

  tags = var.tags
}

resource "null_resource" "k8s_cleanup" {
  triggers = {
    cluster_name = var.cluster_name
    region       = var.region
  }

  provisioner "local-exec" {
    when       = destroy
    on_failure = continue
    command    = <<-EOT
      aws eks update-kubeconfig --name ${self.triggers.cluster_name} --region ${self.triggers.region}
      kubectl get svc --all-namespaces -o json \
        | jq -r '.items[] | select(.spec.type=="LoadBalancer") | "\(.metadata.namespace) \(.metadata.name)"' \
        | xargs -r -L1 bash -c 'kubectl delete svc -n $0 $1'
      sleep 30
    EOT
  }
}
