import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(20, 30))
ax.set_xlim(0, 20)
ax.set_ylim(0, 30)
ax.axis('off')
fig.patch.set_facecolor('#0d1117')

def box(ax, x, y, w, h, color, alpha=1.0, radius=0.3, lw=0, edgecolor='none'):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=color, edgecolor=edgecolor,
                       linewidth=lw, alpha=alpha, zorder=2)
    ax.add_patch(p)

def label(ax, x, y, text, size=9, color='white', weight='normal', ha='center', va='center', zorder=5):
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=zorder, fontfamily='monospace')

def arrow(ax, x1, y1, x2, y2, color='#58a6ff', lw=1.5, style='->', dashed=False):
    ls = 'dashed' if dashed else 'solid'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                linestyle=ls), zorder=4)

C_TEXT   = '#e6edf3'
C_MUTED  = '#8b949e'
C_BLUE   = '#58a6ff'
C_GREEN  = '#3fb950'
C_ORANGE = '#d29922'
C_PURPLE = '#bc8cff'
C_RED    = '#f85149'
C_WAF    = '#e040fb'
C_CW     = '#00bcd4'

# ── TITLE ─────────────────────────────────────────────────────────────────────
ax.text(10, 29.4, 'AWS EKS Cluster — Architecture', fontsize=18, color=C_TEXT,
        fontweight='bold', ha='center', fontfamily='monospace')
ax.text(10, 29.0, 'Region: us-east-1  |  Cluster: my-eks-cluster  |  Terraform-managed',
        fontsize=9, color=C_MUTED, ha='center', fontfamily='monospace')

# ── INTERNET ──────────────────────────────────────────────────────────────────
box(ax, 7.5, 27.5, 5, 0.9, '#161b22', lw=1.5, edgecolor='#30363d')
label(ax, 10, 27.95, 'Internet', size=11, color=C_TEXT, weight='bold')
arrow(ax, 10, 27.5, 10, 26.8)

# ── WAF ───────────────────────────────────────────────────────────────────────
box(ax, 4.5, 25.6, 11, 1.1, '#1c1028', lw=2, edgecolor=C_WAF)
label(ax, 10, 26.3, 'AWS WAFv2  (REGIONAL)', size=10, color=C_WAF, weight='bold')
label(ax, 10, 25.9, 'CommonRuleSet  |  KnownBadInputs  |  Rate Limit: 2000 req/5min', size=7.5, color=C_MUTED)
arrow(ax, 10, 26.8, 10, 26.7)
arrow(ax, 10, 25.6, 10, 24.9)

# ── INTERNET GATEWAY ──────────────────────────────────────────────────────────
box(ax, 7.5, 24.1, 5, 0.75, '#1c2128', lw=1.5, edgecolor=C_ORANGE)
label(ax, 10, 24.47, 'Internet Gateway', size=10, color=C_ORANGE, weight='bold')
arrow(ax, 10, 24.1, 10, 23.4)

# ── CLOUDWATCH (right side) ───────────────────────────────────────────────────
box(ax, 15.5, 19.5, 4.1, 7.5, '#0d1f24', lw=2, edgecolor=C_CW)
label(ax, 17.55, 26.7, 'CloudWatch', size=10, color=C_CW, weight='bold')
label(ax, 17.55, 26.3, 'Logs', size=9, color=C_CW)

box(ax, 15.7, 25.1, 3.7, 0.85, '#0a2a30', lw=1, edgecolor=C_CW)
label(ax, 17.55, 25.52, '/aws/eks/.../cluster', size=7.5, color=C_CW)

box(ax, 15.7, 24.0, 3.7, 0.85, '#0a2a30', lw=1, edgecolor=C_CW)
label(ax, 17.55, 24.42, '/aws/eks/.../application', size=7.5, color=C_CW)

box(ax, 15.7, 22.9, 3.7, 0.85, '#0a2a30', lw=1, edgecolor=C_WAF)
label(ax, 17.55, 23.32, 'aws-waf-logs-...', size=7.5, color=C_WAF)

box(ax, 15.7, 21.8, 3.7, 0.85, '#0a2a30', lw=1, edgecolor=C_BLUE)
label(ax, 17.55, 22.22, '/aws/vpc/.../flow-logs', size=7.5, color=C_BLUE)

label(ax, 17.55, 21.4, 'Retention: 30 days', size=7, color=C_MUTED)
label(ax, 17.55, 21.1, '← EKS  ← WAF  ← VPC', size=6.5, color=C_MUTED)

# ── VPC ───────────────────────────────────────────────────────────────────────
box(ax, 0.4, 1.2, 14.8, 22.0, '#1a3a5c', alpha=0.35, lw=2, edgecolor='#2d5a8e')
label(ax, 1.8, 23.0, 'VPC  10.1.0.0/16', size=9, color='#2d5a8e', weight='bold', ha='left')

# ── PUBLIC SUBNETS ────────────────────────────────────────────────────────────
box(ax, 0.7, 21.0, 8.2, 2.8, '#1a4a2e', alpha=0.5, lw=1.5, edgecolor=C_GREEN)
label(ax, 1.8, 23.6, 'Public Subnet AZ1  10.1.1.0/24', size=8, color=C_GREEN, ha='left')

box(ax, 1.0, 21.3, 3.5, 1.8, '#1a3a2a', lw=1.5, edgecolor=C_GREEN)
label(ax, 2.75, 22.4, 'NAT Gateway', size=9, color=C_GREEN, weight='bold')
label(ax, 2.75, 22.05, '+ Elastic IP', size=8, color=C_MUTED)

box(ax, 4.9, 21.3, 3.7, 1.8, '#1a3a2a', lw=1.5, edgecolor=C_GREEN)
label(ax, 6.75, 22.4, 'AWS Load Balancer', size=9, color=C_GREEN, weight='bold')
label(ax, 6.75, 22.05, '(Grafana)', size=8, color=C_MUTED)

# WAF → ALB dashed
arrow(ax, 6.75, 25.6, 6.75, 23.1, color=C_WAF, lw=1.2, dashed=True)
label(ax, 5.6, 24.35, 'WAF attached', size=7, color=C_WAF)

box(ax, 9.3, 21.0, 5.6, 2.8, '#1a4a2e', alpha=0.5, lw=1.5, edgecolor=C_GREEN)
label(ax, 10.2, 23.6, 'Public Subnet AZ2  10.1.2.0/24', size=8, color=C_GREEN, ha='left')
box(ax, 9.5, 21.3, 5.2, 1.8, '#1a3a2a', lw=1, edgecolor=C_GREEN, alpha=0.4)
label(ax, 12.1, 22.4, '0.0.0.0/0 → IGW', size=8, color=C_GREEN)
label(ax, 12.1, 22.0, 'k8s.io/role/elb=1', size=7.5, color=C_MUTED)

# ── PRIVATE SUBNETS ───────────────────────────────────────────────────────────
box(ax, 0.7, 9.5, 14.1, 11.2, '#1a2a4a', alpha=0.4, lw=1.5, edgecolor=C_BLUE)
label(ax, 1.8, 20.5, 'Private Subnets  AZ1: 10.1.11.0/24  |  AZ2: 10.1.12.0/24', size=8, color=C_BLUE, ha='left')

for nx, az in [(1.0, 'AZ1'), (8.0, 'AZ2')]:
    box(ax, nx, 17.8, 6.5, 2.5, '#1c2a3a', lw=1.5, edgecolor=C_BLUE)
    label(ax, nx+3.25, 19.4, f'Worker Node ({az})  t3.medium', size=9, color=C_BLUE, weight='bold')
    label(ax, nx+3.25, 18.95, 'EKS Managed Node Group', size=8, color=C_MUTED)
    label(ax, nx+3.25, 18.55, 'Private Subnet  |  0.0.0.0/0 → NAT', size=7.5, color=C_MUTED)
    label(ax, nx+3.25, 18.15, '2 vCPU  4 GB RAM', size=7.5, color=C_MUTED)

# Third node AZ3
box(ax, 5.5, 17.2, 4.0, 0.55, '#1a2a3a', lw=1, edgecolor=C_BLUE)
label(ax, 7.5, 17.47, 'desired=2  min=2  max=4  |  AZ3: 10.1.13.0/24', size=8, color=C_MUTED)

# ── MONITORING NAMESPACE ──────────────────────────────────────────────────────
box(ax, 0.9, 10.0, 13.5, 6.9, '#2a1a4a', alpha=0.5, lw=1.5, edgecolor=C_PURPLE)
label(ax, 2.2, 16.7, 'Namespace: monitoring', size=9, color=C_PURPLE, weight='bold', ha='left')

mon_items = [
    ('Prometheus',   '20Gi', '#e6522c', 1.1),
    ('Alertmanager', ' 5Gi', '#e6522c', 4.0),
    ('Grafana',      '10Gi', '#F46800', 6.9),
    ('Loki',         '20Gi', '#F0A830', 9.8),
    ('Promtail',     'DS',   '#00bfb3', 11.0),
]
for name, storage, color, xoff in mon_items:
    box(ax, xoff, 10.3, 2.7, 3.2, '#161b22', lw=1.5, edgecolor=color)
    label(ax, xoff+1.35, 12.1, name, size=8.5, color=color, weight='bold')
    label(ax, xoff+1.35, 11.65, storage, size=8, color=C_MUTED)

box(ax, 1.1, 10.05, 4.0, 0.85, '#1c2128', lw=1, edgecolor=C_ORANGE)
label(ax, 3.1, 10.47, 'LB Controller (kube-system)', size=7.5, color=C_ORANGE)

arrow(ax, 12.35, 11.9, 10.5, 11.9, color='#00bfb3', lw=1.2)
label(ax, 11.4, 12.15, 'logs', size=7, color='#00bfb3')
arrow(ax, 3.7, 11.9, 6.9, 11.9, color=C_MUTED, lw=1)
arrow(ax, 9.65, 11.9, 8.25, 11.9, color=C_MUTED, lw=1)
label(ax, 8.0, 12.15, 'datasources', size=7, color=C_MUTED)

# ── EKS CONTROL PLANE ────────────────────────────────────────────────────────
box(ax, 0.7, 6.0, 14.1, 3.2, '#2a1a1a', alpha=0.6, lw=2, edgecolor=C_ORANGE)
label(ax, 7.75, 9.0, 'EKS Control Plane  (AWS Managed)  |  k8s 1.31', size=10, color=C_ORANGE, weight='bold')
label(ax, 7.75, 8.55, 'Logs: api · audit · authenticator · controllerManager · scheduler → CloudWatch', size=8, color=C_CW)

box(ax, 1.0, 6.3, 4.2, 1.4, '#1c2128', lw=1, edgecolor=C_ORANGE)
label(ax, 3.1, 7.2, 'IAM: eks-cluster-role', size=8, color=C_ORANGE)
label(ax, 3.1, 6.8, 'AmazonEKSClusterPolicy', size=7, color=C_MUTED)

box(ax, 5.6, 6.3, 4.2, 1.4, '#1c2128', lw=1, edgecolor=C_ORANGE)
label(ax, 7.7, 7.2, 'IAM: nodegroup-role', size=8, color=C_ORANGE)
label(ax, 7.7, 6.8, 'EKSWorkerNode+CNI+ECR', size=7, color=C_MUTED)

box(ax, 10.2, 6.3, 4.3, 1.4, '#1c2128', lw=1, edgecolor=C_RED)
label(ax, 12.35, 7.2, 'Security Groups', size=8, color=C_RED)
label(ax, 12.35, 6.8, 'cluster-sg  |  nodes-sg', size=7, color=C_MUTED)

# EKS → CloudWatch arrow
arrow(ax, 14.8, 7.6, 15.5, 22.0, color=C_CW, lw=1.2, dashed=True)

# WAF → CloudWatch (full logs)
arrow(ax, 15.5, 25.6, 15.5, 23.75, color=C_WAF, lw=1.2, dashed=True)

# VPC Flow Logs → CloudWatch
arrow(ax, 14.8, 20.0, 15.5, 22.22, color=C_BLUE, lw=1.2, dashed=True)

# ── S3 BACKEND ───────────────────────────────────────────────────────────────
box(ax, 0.7, 1.4, 14.1, 4.3, '#3a2a1a', alpha=0.5, lw=1.5, edgecolor=C_ORANGE)
label(ax, 7.75, 5.5, 'S3 Bucket — Terraform Remote State', size=10, color=C_ORANGE, weight='bold')

s3_items = [
    ('Versioning',    'Enabled',         C_GREEN),
    ('Encryption',    'AES-256',         C_GREEN),
    ('Public Access', 'Blocked',         C_RED),
    ('force_destroy', 'false',           C_MUTED),
    ('Backend',       'local (bootstrap)', C_BLUE),
]
for i, (k, v, c) in enumerate(s3_items):
    xp = 1.0 + i * 2.7
    box(ax, xp, 1.7, 2.5, 2.2, '#161b22', lw=1, edgecolor=c)
    label(ax, xp+1.25, 3.0, k, size=7.5, color=C_MUTED)
    label(ax, xp+1.25, 2.5, v, size=8, color=c, weight='bold')

# ── CONNECTING ARROWS ─────────────────────────────────────────────────────────
arrow(ax, 7.5, 24.47, 5.5, 23.8, color=C_ORANGE, lw=1.5)
arrow(ax, 12.5, 24.47, 12.5, 23.8, color=C_ORANGE, lw=1.5)
arrow(ax, 2.75, 21.3, 2.75, 20.0, color=C_GREEN, lw=1.5)
arrow(ax, 4.0, 17.8, 4.0, 9.2, color=C_BLUE, lw=1.5)
arrow(ax, 11.5, 17.8, 11.5, 9.2, color=C_BLUE, lw=1.5)
arrow(ax, 7.75, 6.0, 7.75, 5.7, color=C_ORANGE, lw=1.5)

# ── LEGEND ────────────────────────────────────────────────────────────────────
legend_items = [
    (C_GREEN,  'Public Subnet/NAT'),
    (C_BLUE,   'Private Subnet/Nodes'),
    (C_PURPLE, 'Monitoring NS'),
    (C_ORANGE, 'AWS Managed/IAM/S3'),
    (C_WAF,    'WAF (Web ACL)'),
    (C_CW,     'CloudWatch Logs'),
    (C_RED,    'Security Groups'),
]
for i, (c, txt) in enumerate(legend_items):
    bx = 0.3 + i * 2.77
    box(ax, bx, 0.1, 2.6, 0.6, '#161b22', lw=1, edgecolor=c)
    label(ax, bx+1.3, 0.4, txt, size=7, color=c)

plt.tight_layout(pad=0)
plt.savefig('eks-proj.pdf', format='pdf', bbox_inches='tight',
            facecolor=fig.get_facecolor(), dpi=150)
print('PDF saved.')
