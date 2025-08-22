#!/bin/bash

# quanBuy GKE Deployment Script
# This script deploys the quanBuy platform to Google Kubernetes Engine

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"quanbuy-project"}
CLUSTER_NAME=${CLUSTER_NAME:-"quanbuy-cluster"}
REGION=${REGION:-"us-central1"}
NAMESPACE="quanbuy"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting quanBuy GKE Deployment${NC}"
echo "Project: $PROJECT_ID"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed. Please install it first.${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}📋 Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Check if cluster exists, create if not
echo -e "${YELLOW}🔍 Checking if GKE cluster exists...${NC}"
if ! gcloud container clusters describe $CLUSTER_NAME --region=$REGION &> /dev/null; then
    echo -e "${YELLOW}🏗️  Creating GKE Standard cluster with cost-optimized configuration...${NC}"
    
    # Create a cost-optimized GKE Standard cluster
    gcloud container clusters create $CLUSTER_NAME \
        --region=$REGION \
        --num-nodes=1 \
        --machine-type=e2-medium \
        --disk-size=30 \
        --disk-type=pd-standard \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=3 \
        --enable-autorepair \
        --enable-autoupgrade \
        --release-channel=regular \
        --enable-stackdriver-kubernetes \
        --addons=HorizontalPodAutoscaling,HttpLoadBalancing \
        --workload-pool=$PROJECT_ID.svc.id.goog \
        --enable-shielded-nodes
    
    # Create a spot instance node pool for non-critical workloads
    echo -e "${YELLOW}🏗️  Creating Spot VM node pool for cost savings...${NC}"
    gcloud container node-pools create spot-pool \
        --cluster=$CLUSTER_NAME \
        --region=$REGION \
        --machine-type=e2-small \
        --spot \
        --enable-autoscaling \
        --min-nodes=0 \
        --max-nodes=2 \
        --num-nodes=1 \
        --disk-size=30 \
        --disk-type=pd-standard
else
    echo -e "${GREEN}✅ Cluster already exists${NC}"
fi

# Get cluster credentials
echo -e "${YELLOW}🔐 Getting cluster credentials...${NC}"
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required GCP APIs...${NC}"
gcloud services enable \
    container.googleapis.com \
    compute.googleapis.com \
    firestore.googleapis.com \
    pubsub.googleapis.com \
    redis.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com

# Create namespace
echo -e "${YELLOW}📦 Creating namespace...${NC}"
kubectl apply -f kubernetes-manifests/namespace.yaml

# Deploy Redis for caching
echo -e "${YELLOW}🗄️  Deploying Redis...${NC}"
kubectl apply -f kubernetes-manifests/redis.yaml

# Deploy ConfigMaps
echo -e "${YELLOW}⚙️  Creating ConfigMaps...${NC}"
kubectl apply -f kubernetes-manifests/gemini-service/configmap.yaml

# Check for secrets
echo -e "${YELLOW}🔑 Checking for secrets...${NC}"
if ! kubectl get secret gemini-secret -n $NAMESPACE &> /dev/null; then
    echo -e "${RED}⚠️  Warning: gemini-secret not found. Please create it:${NC}"
    echo "kubectl create secret generic gemini-secret --from-literal=api-key=YOUR_GEMINI_API_KEY -n $NAMESPACE"
fi

if ! kubectl get secret gcp-service-account-key -n $NAMESPACE &> /dev/null; then
    echo -e "${RED}⚠️  Warning: gcp-service-account-key not found. Please create it:${NC}"
    echo "kubectl create secret generic gcp-service-account-key --from-file=key.json=path/to/service-account-key.json -n $NAMESPACE"
fi

# Build and push Docker images
echo -e "${YELLOW}🐳 Building and pushing Docker images...${NC}"

# Build Gemini service
echo "Building Gemini service..."
docker build -t gcr.io/$PROJECT_ID/geminiservice:latest src/geminiservice/
docker push gcr.io/$PROJECT_ID/geminiservice:latest

# Build other services (if modified)
# docker build -t gcr.io/$PROJECT_ID/frontend:latest src/frontend/
# docker push gcr.io/$PROJECT_ID/frontend:latest

# Deploy services
echo -e "${YELLOW}🚀 Deploying services...${NC}"

# Deploy existing services
echo "Deploying core services..."
kubectl apply -f kubernetes-manifests/frontend.yaml
kubectl apply -f kubernetes-manifests/currencyservice.yaml
kubectl apply -f kubernetes-manifests/checkoutservice.yaml
kubectl apply -f kubernetes-manifests/quanbuyservice.yaml

# Deploy Gemini service
echo "Deploying Gemini service..."
kubectl apply -f kubernetes-manifests/gemini-service/deployment.yaml
kubectl apply -f kubernetes-manifests/gemini-service/service.yaml
kubectl apply -f kubernetes-manifests/gemini-service/hpa.yaml

# Deploy Ingress
echo -e "${YELLOW}🌐 Deploying Ingress...${NC}"
kubectl apply -f kubernetes-manifests/ingress.yaml

# Wait for deployments to be ready
echo -e "${YELLOW}⏳ Waiting for deployments to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s \
    deployment/geminiservice \
    deployment/frontend \
    deployment/redis \
    -n $NAMESPACE

# Get Ingress IP
echo -e "${YELLOW}🔍 Getting Ingress IP address...${NC}"
INGRESS_IP=$(kubectl get ingress quanbuy-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

if [ "$INGRESS_IP" = "pending" ] || [ -z "$INGRESS_IP" ]; then
    echo -e "${YELLOW}⏳ Ingress IP is still being provisioned. This can take a few minutes.${NC}"
    echo "Run this command to check status:"
    echo "kubectl get ingress quanbuy-ingress -n $NAMESPACE"
else
    echo -e "${GREEN}✅ Ingress IP: $INGRESS_IP${NC}"
fi

# Display status
echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Reserve a static IP: gcloud compute addresses create quanbuy-ip --global"
echo "2. Update DNS records to point to the Ingress IP"
echo "3. Create secrets if not already done:"
echo "   kubectl create secret generic gemini-secret --from-literal=api-key=YOUR_KEY -n $NAMESPACE"
echo ""
echo "Useful commands:"
echo "- View pods: kubectl get pods -n $NAMESPACE"
echo "- View services: kubectl get svc -n $NAMESPACE"
echo "- View logs: kubectl logs -f deployment/geminiservice -n $NAMESPACE"
echo "- Port forward for testing: kubectl port-forward svc/frontend 8080:80 -n $NAMESPACE"
echo ""
echo "Access your application at: http://$INGRESS_IP (once ready)"
