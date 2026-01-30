# FastAPI Marketplace with Google Sheets Backend

A modern marketplace application built with FastAPI, featuring Google Sheets as a backend database, comprehensive monitoring with Prometheus/Grafana, and production-ready Kubernetes deployment.

## 🚀 Features

- **FastAPI Backend**: Modern, fast web framework for building APIs
- **Google Sheets Integration**: Use Google Sheets as a database
- **User Management**: Customer, Seller, and Logist roles
- **Order Management**: Complete order lifecycle management
- **Product Catalog**: Product management with inventory tracking
- **Prometheus Metrics**: Comprehensive application and business metrics
- **Structured Logging**: JSON logging for Loki/Grafana integration
- **Kubernetes Ready**: Helm charts and ArgoCD deployment
- **CI/CD Pipeline**: GitHub Actions with security scanning

## 📊 Monitoring & Observability

### Metrics Available
- Request rate and response time
- User registrations by role
- Order creation and status changes
- Product inventory levels
- Google Sheets operation metrics
- Application health metrics

### Dashboards
- **Grafana**: Business and technical metrics
- **Loki**: Centralized logging
- **Prometheus**: Metrics collection

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.11+
- Docker (for containerization)
- Kubernetes cluster (for deployment)
- Google Cloud Service Account

### 2. Google Sheets Setup

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a Service Account
4. Download credentials JSON file
5. Copy credentials:
   ```bash
   cp credentials.json.example credentials.json
   # Edit credentials.json with your actual credentials
   ```

6. Create a Google Sheet named "marketplace" with these worksheets:
   - **Users**: ID, username, password_hash, role, full_name, phone, created_at
   - **Products**: id, seller_id, name, price, description, stock, image_url, created_at
   - **Orders**: id, customer_id, seller_id, product_id, quantity, total_price, status, logist_id, customer_phone, seller_phone, created_at, updated_at

### 3. Local Development

```bash
# Clone repository
git clone https://github.com/your-org/marketplace.git
cd marketplace

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

Access the application:
- **Main App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics
- **Health Check**: http://localhost:8000/api/test

### 4. Docker Development

```bash
# Build image
docker build -t marketplace-app .

# Run container
docker run -p 8000:8000 -v $(pwd)/credentials.json:/app/credentials.json marketplace-app
```

### 5. Monitoring Stack (Local)

```bash
# Start monitoring services
docker-compose up -d

# Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Loki: http://localhost:3100
```

## 🚢 Deployment

### Kubernetes Deployment

1. **Create namespace and secrets:**
   ```bash
   kubectl create namespace marketplace-dev
   kubectl create secret generic google-sheets-credentials \
     --from-file=credentials.json=./credentials.json \
     -n marketplace-dev
   ```

2. **Deploy with Helm:**
   ```bash
   helm upgrade --install marketplace-dev ./deploy/helm/marketplace \
     -f ./deploy/helm/marketplace/values-dev.yaml \
     -n marketplace-dev
   ```

3. **Setup ArgoCD (GitOps):**
   ```bash
   kubectl apply -f deploy/argocd/marketplace-dev.yaml
   ```

### CI/CD Pipeline

The GitHub Actions workflow automatically:
1. Builds and tests the application
2. Creates Docker image
3. Runs security scans with Trivy
4. Pushes to Docker Hub
5. Updates Helm values for GitOps
6. Triggers ArgoCD deployment

**Required GitHub Secrets:**
- `DOCKER_HUB_USERNAME`
- `DOCKER_HUB_PASSWORD`

## 📁 Project Structure

```
├── main.py                 # FastAPI application
├── sheets.py              # Google Sheets integration
├── metrics.py             # Prometheus metrics
├── logging_config.py      # Structured logging
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Local monitoring stack
├── .github/
│   └── workflows/
│       └── deploy.yml    # CI/CD pipeline
├── deploy/
│   ├── helm/
│   │   └── marketplace/  # Helm chart
│   └── argocd/          # ArgoCD applications
├── grafana/             # Grafana configuration
├── static/              # Frontend files
└── logs/               # Application logs
```

## 🔧 Configuration

### Environment Variables
- `ENVIRONMENT`: deployment environment (dev/staging/prod)
- `LOG_LEVEL`: logging level (DEBUG/INFO/WARNING/ERROR)

### Helm Values
Customize deployment in `values-{env}.yaml` files:
- Resource limits and requests
- Replica count and autoscaling
- Ingress configuration
- Monitoring settings

## 🔒 Security

- **Container Security**: Non-root user, minimal base image
- **Secret Management**: Kubernetes secrets for credentials
- **Network Policies**: Restrict pod-to-pod communication
- **Security Scanning**: Automated Trivy scans in CI/CD
- **RBAC**: Proper service account permissions

## 📈 Scaling

### Horizontal Pod Autoscaler
Automatically scales based on:
- CPU utilization (70% threshold)
- Memory utilization (80% threshold)

### Manual Scaling
```bash
kubectl scale deployment marketplace-dev --replicas=5 -n marketplace-dev
```

## 🐛 Troubleshooting

### Common Issues

1. **Google Sheets Authentication Error**
   ```bash
   # Check if credentials secret exists
   kubectl get secret google-sheets-credentials -n marketplace-dev
   
   # Verify credentials are mounted
   kubectl exec -it deployment/marketplace-dev -- ls -la /app/credentials.json
   ```

2. **Health Check Failures**
   ```bash
   # Check application logs
   kubectl logs -f deployment/marketplace-dev -n marketplace-dev
   
   # Test health endpoint
   kubectl port-forward svc/marketplace-dev 8000:80 -n marketplace-dev
   curl http://localhost:8000/api/test
   ```

3. **Metrics Not Available**
   ```bash
   # Check metrics endpoint
   curl http://localhost:8000/metrics
   
   # Verify ServiceMonitor
   kubectl get servicemonitor -n marketplace-dev
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in GitHub
- Contact the DevOps team
- Check the deployment documentation in `DEPLOYMENT.md`