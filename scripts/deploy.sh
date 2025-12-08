#!/bin/bash
# Deployment script for Powerhouse Platform

set -e

ENVIRONMENT=${1:-staging}
NAMESPACE="powerhouse"

echo "🚀 Deploying Powerhouse Platform to ${ENVIRONMENT}..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if namespace exists, create if not
if ! kubectl get namespace ${NAMESPACE} &> /dev/null; then
    echo "📦 Creating namespace ${NAMESPACE}..."
    kubectl apply -f k8s/namespace.yaml
fi

# Apply configurations
echo "⚙️  Applying configurations..."
kubectl apply -f k8s/configmap.yaml

# Check if secrets exist
if ! kubectl get secret powerhouse-secrets -n ${NAMESPACE} &> /dev/null; then
    echo "⚠️  Secrets not found. Please create k8s/secret.yaml from k8s/secret.yaml.example"
    echo "   Then run: kubectl apply -f k8s/secret.yaml"
    exit 1
fi

# Deploy PostgreSQL
echo "🐘 Deploying PostgreSQL..."
kubectl apply -f k8s/postgres-deployment.yaml

# Deploy Redis
echo "📦 Deploying Redis..."
kubectl apply -f k8s/redis-deployment.yaml

# Wait for dependencies
echo "⏳ Waiting for dependencies to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n ${NAMESPACE} --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n ${NAMESPACE} --timeout=300s

# Deploy Backend
echo "🔧 Deploying Backend..."
kubectl apply -f k8s/backend-deployment.yaml

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
kubectl wait --for=condition=ready pod -l app=powerhouse-backend -n ${NAMESPACE} --timeout=300s

# Deploy Ingress (if not in local/dev)
if [ "${ENVIRONMENT}" != "local" ]; then
    echo "🌐 Deploying Ingress..."
    kubectl apply -f k8s/ingress.yaml
fi

echo "✅ Deployment complete!"
echo ""
echo "📊 Check status with:"
echo "   kubectl get pods -n ${NAMESPACE}"
echo "   kubectl get services -n ${NAMESPACE}"
echo ""
echo "📝 View logs with:"
echo "   kubectl logs -f deployment/powerhouse-backend -n ${NAMESPACE}"

