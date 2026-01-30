# Marketplace Deployment Guide

## Overview
This document describes the deployment process for the FastAPI Marketplace application using Kubernetes, Helm, ArgoCD, and GitHub Actions.

## Architecture
- **Application**: FastAPI with Google Sheets backend
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **Package Manager**: Helm
- **GitOps**: ArgoCD
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: Loki + Promtail

## Prerequisites

### 1. Docker Hub Setup
Create secrets in GitHub repository:
```bash
DOCKER_HUB_USERNAME=your-username
DOCKER_HUB_PASSWORD=your-password
```

### 2. Google Sheets Credentials
Create a Kubernetes secret with Google Sheets credentials:
```bash
kubectl create secret generic google-sheets-credentials \
  --from-file=credentials.json=./credentials.json \
  -n marketplace-dev
```

### 3. ArgoCD Setup
Apply ArgoCD applications:
```bash
kubectl apply -f deploy/argocd/marketplace-dev.yaml
kubectl apply -f deploy/argocd/marketplace-staging.yaml
kubectl apply -f deploy/argocd/marketplace-prod.yaml
```

## Deployment Process

### Automatic Deployment (GitOps)
1. **Push to main branch** → Triggers CI/CD pipeline
2. **GitHub Actions** builds and pushes Docker image
3. **Helm values** are updated with new image tag
4. **ArgoCD** detects changes and syncs automatically

### Manual Deployment
Use GitHub Actions workflow dispatch:
1. Go to Actions tab in GitHub
2. Select "FastAPI Marketplace CI/CD"
3. Click "Run workflow"
4. Choose environment and deployment option

## Environments

### Development
- **Namespace**: `marketplace-dev`
- **URL**: `https://marketplace-dev.company.com`
- **Auto-sync**: Enabled
- **Replicas**: 1

### Staging
- **Namespace**: `marketplace-staging`
- **URL**: `https://marketplace-staging.company.com`
- **Auto-sync**: Enabled
- **Replicas**: 2

### Production
- **Namespace**: `marketplace-prod`
- **URL**: `https://marketplace.company.com`
- **Auto-sync**: Manual approval required
- **Replicas**: 3

## Monitoring Setup

### 1. Deploy Monitoring Stack
```bash
# Deploy Prometheus, Grafana, Loki
docker-compose up -d

# Or use Helm charts for Kubernetes
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts

helm install prometheus prometheus-community/kube-prometheus-stack
helm install loki grafana/loki-stack
```

### 2. Access Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

### 3. Application Metrics
Available at: `http://your-app:8000/metrics`

Key metrics:
- `marketplace_requests_total` - Request count
- `marketplace_request_duration_seconds` - Response time
- `marketplace_user_registrations_total` - User registrations
- `marketplace_orders_created_total` - Orders created
- `marketplace_active_users` - Active users by role
- `marketplace_google_sheets_operations_total` - Google Sheets operations

## Helm Commands

### Install/Upgrade
```bash
# Development
helm upgrade --install marketplace-dev ./deploy/helm/marketplace \
  -f ./deploy/helm/marketplace/values-dev.yaml \
  -n marketplace-dev --create-namespace

# Staging
helm upgrade --install marketplace-staging ./deploy/helm/marketplace \
  -f ./deploy/helm/marketplace/values-staging.yaml \
  -n marketplace-staging --create-namespace

# Production
helm upgrade --install marketplace-prod ./deploy/helm/marketplace \
  -f ./deploy/helm/marketplace/values-prod.yaml \
  -n marketplace-prod --create-namespace
```

### Debug
```bash
# Dry run
helm install marketplace-dev ./deploy/helm/marketplace \
  -f ./deploy/helm/marketplace/values-dev.yaml \
  --dry-run --debug

# Template rendering
helm template marketplace-dev ./deploy/helm/marketplace \
  -f ./deploy/helm/marketplace/values-dev.yaml
```

## Troubleshooting

### Check Application Status
```bash
kubectl get pods -n marketplace-dev
kubectl logs -f deployment/marketplace-dev -n marketplace-dev
kubectl describe pod <pod-name> -n marketplace-dev
```

### Check ArgoCD Sync Status
```bash
argocd app get marketplace-dev
argocd app sync marketplace-dev
argocd app logs marketplace-dev
```

### Check Metrics
```bash
# Port forward to access metrics
kubectl port-forward svc/marketplace-dev 8000:80 -n marketplace-dev
curl http://localhost:8000/metrics
```

### Common Issues

1. **Google Sheets Authentication**
   - Ensure credentials.json is properly mounted
   - Check secret exists: `kubectl get secret google-sheets-credentials -n marketplace-dev`

2. **Image Pull Errors**
   - Verify Docker Hub credentials
   - Check image tag in values file

3. **Health Check Failures**
   - Check `/api/test` endpoint
   - Verify Google Sheets connectivity

## Security Considerations

1. **Secrets Management**
   - Use Kubernetes secrets for sensitive data
   - Consider using external secret management (Vault, etc.)

2. **Network Policies**
   - Implement network policies to restrict traffic
   - Use service mesh for advanced security

3. **RBAC**
   - Configure proper RBAC for service accounts
   - Limit permissions to minimum required

4. **Image Security**
   - Trivy scans are automated in CI/CD
   - Regular base image updates
   - Non-root container execution

## Scaling

### Horizontal Pod Autoscaler
HPA is configured to scale based on:
- CPU utilization (70%)
- Memory utilization (80%)

### Manual Scaling
```bash
kubectl scale deployment marketplace-dev --replicas=5 -n marketplace-dev
```

## Backup and Recovery

### Database Backup
Since using Google Sheets, ensure:
- Regular Google Sheets backups
- Export important data periodically

### Configuration Backup
- Helm values are version controlled
- Kubernetes manifests in Git
- ArgoCD applications in Git