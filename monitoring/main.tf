########################
# gp3 StorageClass
########################

resource "kubernetes_storage_class" "gp3" {
  metadata {
    name = "gp3"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true

  parameters = {
    type      = "gp3"
    encrypted = "true"
  }
}

########################
# Monitoring namespace
########################

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
}

########################
# AWS Load Balancer Controller
########################

resource "helm_release" "aws_lb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.7.2"

  set {
    name  = "clusterName"
    value = var.cluster_name
  }

  set {
    name  = "serviceAccount.create"
    value = "true"
  }
}

########################
# kube-prometheus-stack (Prometheus + Grafana + Alertmanager)
########################

resource "helm_release" "kube_prometheus_stack" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "58.2.2"

  values = [
    yamlencode({
      grafana = {
        adminPassword = var.grafana_admin_password
        service = {
          type = "LoadBalancer"
          annotations = {
            "service.beta.kubernetes.io/aws-load-balancer-type"   = "external"
            "service.beta.kubernetes.io/aws-load-balancer-scheme" = "internet-facing"
          }
        }
        persistence = {
          enabled          = true
          storageClassName = "gp3"
          size             = "10Gi"
        }
      }
      prometheus = {
        prometheusSpec = {
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = "gp3"
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = { storage = "20Gi" }
                }
              }
            }
          }
        }
      }
      alertmanager = {
        alertmanagerSpec = {
          storage = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = "gp3"
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = { storage = "5Gi" }
                }
              }
            }
          }
        }
      }
    })
  ]

  depends_on = [kubernetes_storage_class.gp3]
}

########################
# Loki Stack
########################

resource "helm_release" "loki" {
  name       = "loki"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "2.10.2"

  values = [
    yamlencode({
      loki = {
        persistence = {
          enabled          = true
          storageClassName = "gp3"
          size             = "20Gi"
        }
      }
      promtail = {
        enabled = true
      }
      grafana = {
        enabled = false # already deployed via kube-prometheus-stack
      }
    })
  ]

  depends_on = [
    kubernetes_storage_class.gp3,
    helm_release.kube_prometheus_stack,
  ]
}
