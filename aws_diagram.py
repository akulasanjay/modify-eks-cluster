from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import VPC, InternetGateway, NATGateway, ElasticLoadBalancing
from diagrams.aws.security import WAF, IAMRole
from diagrams.aws.compute import EKS, EC2
from diagrams.aws.management import Cloudwatch
from diagrams.aws.storage import S3
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.logging import Loki
from diagrams.k8s.compute import Pod

graph_attr = {
    "fontsize": "18",
    "bgcolor": "#0d1117",
    "fontcolor": "#e6edf3",
    "pad": "0.6",
    "splines": "ortho",
    "nodesep": "0.7",
    "ranksep": "0.9",
    "fontname": "Helvetica",
}

node_attr = {
    "fontcolor": "#e6edf3",
    "fontsize": "11",
    "fontname": "Helvetica",
}

with Diagram(
    "AWS EKS Cluster Architecture\nRegion: us-east-1  |  Cluster: my-eks-cluster  |  Kubernetes 1.31",
    filename="eks_architecture",
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
):
    waf = WAF("AWS WAFv2\nCommonRules · KnownBadInputs\nRate Limit: 2000 req/5min")
    igw = InternetGateway("Internet Gateway")
    s3  = S3("S3 Remote State\nVersioning + AES-256\nPublic Access Blocked")

    with Cluster("CloudWatch Logs  (30-day retention)",
                 graph_attr={"bgcolor": "#0d1f24", "fontcolor": "#00bcd4", "style": "rounded"}):
        cw_eks  = Cloudwatch("EKS Control Plane\n/eks/.../cluster\napi·audit·authenticator\ncontrollerManager·scheduler")
        cw_app  = Cloudwatch("Application\n/eks/.../application")
        cw_waf  = Cloudwatch("WAF Full Logs\naws-waf-logs-...\nIPs·URIs·matched rules")
        cw_vpc  = Cloudwatch("VPC Flow Logs\n/aws/vpc/.../flow-logs\nALL traffic (accept+reject)")

    with Cluster("VPC  10.1.0.0/16",
                 graph_attr={"bgcolor": "#0d1a2e", "fontcolor": "#58a6ff", "style": "rounded"}):

        with Cluster("Public Subnets  AZ1–AZ3  (10.1.1–3.0/24)",
                     graph_attr={"bgcolor": "#0d1f14", "fontcolor": "#3fb950", "style": "rounded"}):
            nat = NATGateway("NAT Gateway\n+ Elastic IP")
            alb = ElasticLoadBalancing("AWS Load Balancer\nGrafana  |  k8s.io/role/elb=1")

        with Cluster("Private Subnets  AZ1–AZ3  (10.1.11–13.0/24)",
                     graph_attr={"bgcolor": "#0d1a2e", "fontcolor": "#58a6ff", "style": "rounded"}):

            with Cluster("EKS Managed Node Group  |  desired=2  min=2  max=4",
                         graph_attr={"bgcolor": "#0d1a3a", "fontcolor": "#58a6ff", "style": "rounded"}):
                nodes = [
                    EC2("Worker Node AZ1\nt3.medium\n2vCPU · 4GB\n10.1.11.0/24"),
                    EC2("Worker Node AZ2\nt3.medium\n2vCPU · 4GB\n10.1.12.0/24"),
                    EC2("Worker Node AZ3\nt3.medium\n2vCPU · 4GB\n10.1.13.0/24"),
                ]

            with Cluster("Namespace: monitoring",
                         graph_attr={"bgcolor": "#1a1030", "fontcolor": "#bc8cff", "style": "rounded"}):
                prom     = Prometheus("Prometheus\n20Gi PVC")
                alert    = Pod("Alertmanager\n5Gi PVC")
                graf     = Grafana("Grafana\n10Gi PVC")
                loki     = Loki("Loki\n20Gi PVC")
                promtail = Pod("Promtail\nDaemonSet")

            with Cluster("EKS Control Plane  (AWS Managed  |  k8s 1.31)",
                         graph_attr={"bgcolor": "#1c1a10", "fontcolor": "#d29922", "style": "rounded"}):
                eks         = EKS("EKS Cluster\nmy-eks-cluster")
                iam_cluster = IAMRole("eks-cluster-role\nAmazonEKSClusterPolicy")
                iam_node    = IAMRole("nodegroup-role\nEKSWorkerNode+CNI+ECR")

    # ── traffic flow ──
    waf >> igw
    igw >> nat
    igw >> Edge(style="dashed", color="#e040fb", label="WAF attached") >> alb
    nat >> nodes[0]
    nat >> nodes[1]
    nat >> nodes[2]
    alb >> graf

    # nodes host monitoring
    for n in nodes:
        n >> Edge(color="#bc8cff", style="dashed") >> prom

    promtail >> Edge(color="#00bfb3", label="logs") >> loki
    loki     >> Edge(color="#00bfb3") >> graf
    prom     >> Edge(color="#e6522c", label="metrics") >> graf
    prom     >> Edge(color="#e6522c") >> alert

    # EKS → CloudWatch
    eks >> Edge(style="dashed", color="#00bcd4", label="control plane logs") >> cw_eks
    eks >> Edge(style="dashed", color="#00bcd4") >> cw_app
    iam_cluster >> Edge(color="#d29922") >> eks
    iam_node    >> Edge(color="#d29922") >> nodes[0]

    # WAF → CloudWatch full logs
    waf >> Edge(style="dashed", color="#e040fb", label="full request logs") >> cw_waf

    # VPC Flow Logs
    igw >> Edge(style="dashed", color="#58a6ff", label="flow logs") >> cw_vpc

    # Terraform state
    eks >> Edge(style="dashed", color="#d29922", label="tfstate") >> s3

print("Saved: eks_architecture.png")
