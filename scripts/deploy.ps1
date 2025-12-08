# PowerShell deployment script for Powerhouse Platform

param(
    [string]$Environment = "staging",
    [string]$Namespace = "powerhouse"
)

Write-Host "🚀 Deploying Powerhouse Platform to $Environment..." -ForegroundColor Cyan

# Check if kubectl is available
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "❌ kubectl is not installed. Please install kubectl first." -ForegroundColor Red
    exit 1
}

# Check if namespace exists, create if not
$namespaceExists = kubectl get namespace $Namespace 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "📦 Creating namespace $Namespace..." -ForegroundColor Yellow
    kubectl apply -f k8s/namespace.yaml
}

# Apply configurations
Write-Host "⚙️  Applying configurations..." -ForegroundColor Yellow
kubectl apply -f k8s/configmap.yaml

# Check if secrets exist
$secretsExist = kubectl get secret powerhouse-secrets -n $Namespace 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Secrets not found. Please create k8s/secret.yaml from k8s/secret.yaml.example" -ForegroundColor Yellow
    Write-Host "   Then run: kubectl apply -f k8s/secret.yaml" -ForegroundColor Yellow
    exit 1
}

# Deploy PostgreSQL
Write-Host "🐘 Deploying PostgreSQL..." -ForegroundColor Yellow
kubectl apply -f k8s/postgres-deployment.yaml

# Deploy Redis
Write-Host "📦 Deploying Redis..." -ForegroundColor Yellow
kubectl apply -f k8s/redis-deployment.yaml

# Wait for dependencies
Write-Host "⏳ Waiting for dependencies to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=postgres -n $Namespace --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n $Namespace --timeout=300s

# Deploy Backend
Write-Host "🔧 Deploying Backend..." -ForegroundColor Yellow
kubectl apply -f k8s/backend-deployment.yaml

# Wait for backend to be ready
Write-Host "⏳ Waiting for backend to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=powerhouse-backend -n $Namespace --timeout=300s

# Deploy Ingress (if not in local/dev)
if ($Environment -ne "local") {
    Write-Host "🌐 Deploying Ingress..." -ForegroundColor Yellow
    kubectl apply -f k8s/ingress.yaml
}

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Check status with:" -ForegroundColor Cyan
Write-Host "   kubectl get pods -n $Namespace"
Write-Host "   kubectl get services -n $Namespace"
Write-Host ""
Write-Host "📝 View logs with:" -ForegroundColor Cyan
Write-Host "   kubectl logs -f deployment/powerhouse-backend -n $Namespace"

