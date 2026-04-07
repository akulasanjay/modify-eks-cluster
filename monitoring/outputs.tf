output "grafana_service" {
  description = "Run this to get the Grafana LoadBalancer URL"
  value       = "kubectl get svc -n monitoring kube-prometheus-stack-grafana -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"
}
