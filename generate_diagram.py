import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(20, 26))
ax.set_xlim(0, 20)
ax.set_ylim(0, 26)
ax.axis('off')
fig.patch.set_facecolor('#0d1117')

# ── helpers ──────────────────────────────────────────────────────────────────
def box(ax, x, y, w, h, color, alpha=1.0, radius=0.3, lw=0, edgecolor='none'):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=color, edgecolor=edgecolor,
                       linewidth=lw, alpha=alpha, zorder=2)
    ax.add_patch(p)

def label(ax, x, y, text, size=9, color='white', weight='normal', ha='center', va='center', zorder=5):
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=zorder, fontfamily='monospace')

def arrow(ax, x1, y1, x2, y2, color='#58a6ff', lw=1.5, style='->', zorder=4):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw), zorder=zorder)

# ── colour palette ────────────────────────────────────────────────────────────
C_AWS      = '#FF9900'
C_EKS      = '#FF9900'
C_VPC      = '#1a3a5c'
C_PUB      = '#1a4a2e'
C_PRIV     = '#1a2a4a'
C_MON      = '#2a1a4a'
C_S3       = '#3a2a1a'
C_CTRL     = '#2a1a1a'
C_BORDER   = '#30363d'
C_TEXT     = '#e6edf3'
C_MUTED    = '#8b949e'
C_BLUE     = '#58a6ff'
C_GREEN    = '#3fb950'
C_ORANGE   = '#d29922'
C_PURPLE   = '#bc8cff'
C_RED      = '#f85149'

# ═══════════════════════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════════════════════
ax.text(10, 25.4, 'AWS EKS Cluster — Architecture', fontsize=18, color=C_TEXT,
        fontweight='bold', ha='center', va='center', fontfamily='monospace')
ax.text(10, 25.0, 'Region: us-east-1  |  Cluster: my-eks-cluster  |  Terraform-managed',
        fontsize=9, color=C_MUTED, ha='center', va='center', fontfamily='monospace')

# ═══════════════════════════════════════════════════════════════════════════════
# INTERNET
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 7.5, 23.8, 5, 0.9, '#161b22', lw=1.5, edgecolor=C_BORDER)
label(ax, 10, 24.25, 'Internet', size=11, color=C_TEXT, weight='bold')

arrow(ax, 10, 23.8, 10, 23.1)

# ═══════════════════════════════════════════════════════════════════════════════
# INTERNET GATEWAY
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 7.5, 22.3, 5, 0.75, '#1c2128', lw=1.5, edgecolor=C_ORANGE)
label(ax, 10, 22.67, '⚡  Internet Gateway', size=10, color=C_ORANGE, weight='bold')

arrow(ax, 10, 22.3, 10, 21.6)

# ═══════════════════════════════════════════════════════════════════════════════
# VPC OUTER BOX
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 0.4, 1.2, 19.2, 20.3, C_VPC, alpha=0.35, lw=2, edgecolor='#2d5a8e')
label(ax, 1.8, 21.3, 'VPC  10.1.0.0/16', size=9, color='#2d5a8e', weight='bold', ha='left')

# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC SUBNETS ROW
# ═══════════════════════════════════════════════════════════════════════════════
# AZ1 public
box(ax, 0.7, 18.5, 8.5, 2.8, C_PUB, alpha=0.5, lw=1.5, edgecolor='#3fb950')
label(ax, 1.8, 21.1, 'Public Subnet AZ1  10.1.1.0/24', size=8, color=C_GREEN, ha='left')

# NAT Gateway
box(ax, 1.0, 18.8, 3.8, 1.8, '#1a3a2a', lw=1.5, edgecolor=C_GREEN)
label(ax, 2.9, 19.9, 'NAT Gateway', size=9, color=C_GREEN, weight='bold')
label(ax, 2.9, 19.55, '+ Elastic IP', size=8, color=C_MUTED)

# ALB in AZ1 public
box(ax, 5.2, 18.8, 3.7, 1.8, '#1a3a2a', lw=1.5, edgecolor=C_GREEN)
label(ax, 7.05, 19.9, 'AWS Load Balancer', size=9, color=C_GREEN, weight='bold')
label(ax, 7.05, 19.55, '(Grafana)', size=8, color=C_MUTED)

# AZ2 public
box(ax, 9.8, 18.5, 9.8, 2.8, C_PUB, alpha=0.5, lw=1.5, edgecolor='#3fb950')
label(ax, 10.9, 21.1, 'Public Subnet AZ2  10.1.2.0/24', size=8, color=C_GREEN, ha='left')

# Route table note
box(ax, 10.1, 18.8, 9.2, 1.8, '#1a3a2a', lw=1, edgecolor='#3fb950', alpha=0.4)
label(ax, 14.7, 19.9, 'Route Table: 0.0.0.0/0 → IGW', size=8.5, color=C_GREEN)
label(ax, 14.7, 19.5, 'Tagged: kubernetes.io/role/elb=1', size=8, color=C_MUTED)

# ═══════════════════════════════════════════════════════════════════════════════
# PRIVATE SUBNETS ROW
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 0.7, 7.5, 18.9, 10.7, C_PRIV, alpha=0.4, lw=1.5, edgecolor='#58a6ff')
label(ax, 1.8, 18.0, 'Private Subnets  AZ1: 10.1.11.0/24  |  AZ2: 10.1.12.0/24', size=8, color=C_BLUE, ha='left')

# Worker nodes
for i, (nx, az) in enumerate([(1.0, 'AZ1'), (10.0, 'AZ2')]):
    box(ax, nx, 15.5, 8.5, 2.2, '#1c2a3a', lw=1.5, edgecolor=C_BLUE)
    label(ax, nx+4.25, 16.85, f'Worker Node ({az})  t3.small', size=9, color=C_BLUE, weight='bold')
    label(ax, nx+4.25, 16.45, 'EKS Managed Node Group  |  Private Subnet', size=8, color=C_MUTED)
    label(ax, nx+4.25, 16.05, 'Route: 0.0.0.0/0 → NAT Gateway', size=8, color=C_MUTED)

# Scaling config badge
box(ax, 7.5, 14.9, 5, 0.55, '#1a2a3a', lw=1, edgecolor=C_BLUE)
label(ax, 10, 15.17, 'Scaling: desired=2  min=2  max=4  |  max_unavailable=1', size=8, color=C_MUTED)

# ── MONITORING NAMESPACE ──────────────────────────────────────────────────────
box(ax, 0.9, 8.0, 18.3, 6.6, C_MON, alpha=0.5, lw=1.5, edgecolor=C_PURPLE)
label(ax, 2.0, 14.4, 'Namespace: monitoring', size=9, color=C_PURPLE, weight='bold', ha='left')

mon_items = [
    ('Prometheus',    '20 Gi gp3', '#e6522c', 1.1),
    ('Alertmanager',  ' 5 Gi gp3', '#e6522c', 4.7),
    ('Grafana',       '10 Gi gp3', '#F46800', 8.3),
    ('Loki',          '20 Gi gp3', '#F0A830', 11.9),
    ('Promtail\n(DaemonSet)', '—', '#00bfb3', 15.5),
]
for name, storage, color, xoff in mon_items:
    box(ax, xoff, 8.3, 3.2, 3.0, '#161b22', lw=1.5, edgecolor=color)
    label(ax, xoff+1.6, 10.15, name, size=9, color=color, weight='bold')
    label(ax, xoff+1.6, 9.65, storage, size=8, color=C_MUTED)

# LB Controller
box(ax, 1.1, 8.05, 4.5, 0.9, '#1c2128', lw=1, edgecolor=C_ORANGE)
label(ax, 3.35, 8.5, 'LB Controller (kube-system)', size=8, color=C_ORANGE)

# Promtail → Loki arrow
arrow(ax, 16.7, 9.8, 13.1, 9.8, color='#00bfb3', lw=1.2)
label(ax, 14.9, 10.05, 'ships logs', size=7.5, color='#00bfb3')

# Grafana datasource arrows
arrow(ax, 4.7, 9.8, 8.3, 9.8, color=C_MUTED, lw=1, style='->')
arrow(ax, 13.1, 9.8, 11.5, 9.8, color=C_MUTED, lw=1, style='->')
label(ax, 9.9, 10.05, 'datasources', size=7.5, color=C_MUTED)

# ═══════════════════════════════════════════════════════════════════════════════
# EKS CONTROL PLANE
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 0.7, 4.5, 18.9, 2.7, C_CTRL, alpha=0.6, lw=2, edgecolor=C_ORANGE)
label(ax, 10, 7.0, 'EKS Control Plane  (AWS Managed)', size=11, color=C_ORANGE, weight='bold')
label(ax, 10, 6.55, 'Private endpoint: ✓   Public endpoint: ✓   API port: 443', size=8.5, color=C_MUTED)

# IAM roles
box(ax, 1.0, 4.75, 5.5, 1.4, '#1c2128', lw=1, edgecolor=C_ORANGE)
label(ax, 3.75, 5.65, 'IAM: eks-cluster-role', size=8.5, color=C_ORANGE)
label(ax, 3.75, 5.25, 'AmazonEKSClusterPolicy', size=7.5, color=C_MUTED)

box(ax, 7.2, 4.75, 5.5, 1.4, '#1c2128', lw=1, edgecolor=C_ORANGE)
label(ax, 9.95, 5.65, 'IAM: nodegroup-role', size=8.5, color=C_ORANGE)
label(ax, 9.95, 5.25, 'EKSWorkerNode + CNI + ECR', size=7.5, color=C_MUTED)

# Security groups
box(ax, 13.4, 4.75, 5.8, 1.4, '#1c2128', lw=1, edgecolor=C_RED)
label(ax, 16.3, 5.65, 'Security Groups', size=8.5, color=C_RED)
label(ax, 16.3, 5.25, 'cluster-sg  |  nodes-sg', size=7.5, color=C_MUTED)

# ═══════════════════════════════════════════════════════════════════════════════
# S3 BACKEND
# ═══════════════════════════════════════════════════════════════════════════════
box(ax, 0.7, 1.4, 18.9, 2.8, C_S3, alpha=0.5, lw=1.5, edgecolor=C_ORANGE)
label(ax, 10, 4.0, 'S3 Bucket — Terraform Remote State', size=10, color=C_ORANGE, weight='bold')

s3_items = [
    ('Versioning', 'Enabled', C_GREEN),
    ('Encryption', 'AES-256', C_GREEN),
    ('Public Access', 'Blocked', C_RED),
    ('force_destroy', 'false', C_MUTED),
    ('Backend', 'local (bootstrap)', C_BLUE),
]
for i, (k, v, c) in enumerate(s3_items):
    xp = 1.5 + i * 3.7
    box(ax, xp, 1.65, 3.3, 1.8, '#161b22', lw=1, edgecolor=c)
    label(ax, xp+1.65, 2.75, k, size=8.5, color=C_MUTED)
    label(ax, xp+1.65, 2.3, v, size=9, color=c, weight='bold')

# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTING ARROWS
# ═══════════════════════════════════════════════════════════════════════════════
# IGW → public subnets
arrow(ax, 7.5, 22.67, 5.2, 21.3, color=C_ORANGE, lw=1.5)
arrow(ax, 12.5, 22.67, 14.7, 21.3, color=C_ORANGE, lw=1.5)

# NAT → private
arrow(ax, 2.9, 18.8, 2.9, 17.7, color=C_GREEN, lw=1.5)

# Worker nodes → EKS control plane
arrow(ax, 5.25, 15.5, 5.25, 7.2, color=C_BLUE, lw=1.5)
arrow(ax, 14.75, 15.5, 14.75, 7.2, color=C_BLUE, lw=1.5)

# Control plane → S3
arrow(ax, 10, 4.5, 10, 4.2, color=C_ORANGE, lw=1.5)

# ═══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════════════════════
legend_items = [
    (C_GREEN,  'Public Subnet / NAT'),
    (C_BLUE,   'Private Subnet / Worker Nodes'),
    (C_PURPLE, 'Monitoring Namespace'),
    (C_ORANGE, 'AWS Managed / IAM / S3'),
    (C_RED,    'Security Groups'),
]
for i, (c, txt) in enumerate(legend_items):
    bx = 0.7 + i * 3.85
    box(ax, bx, 0.15, 3.5, 0.6, '#161b22', lw=1, edgecolor=c)
    label(ax, bx+1.75, 0.45, txt, size=7.5, color=c)

plt.tight_layout(pad=0)
plt.savefig('eks-proj.pdf', format='pdf', bbox_inches='tight',
            facecolor=fig.get_facecolor(), dpi=150)
print('PDF saved: eks-proj.pdf')
