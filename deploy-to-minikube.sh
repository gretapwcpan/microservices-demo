#!/bin/bash

# quanBuy Minikube Local Deployment Script
# End-to-end testing with Kubernetes locally

set -e

# Configuration
NAMESPACE="quanbuy"
REGISTRY="minikube"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting quanBuy Minikube Deployment${NC}"
echo ""

# Check if minikube is installed
if ! command -v minikube &> /dev/null; then
    echo -e "${RED}❌ Minikube is not installed.${NC}"
    echo "Install with: brew install minikube (macOS)"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed.${NC}"
    exit 1
fi

# Start Minikube if not running
echo -e "${YELLOW}🔍 Checking Minikube status...${NC}"
if ! minikube status &> /dev/null; then
    echo -e "${YELLOW}🏗️  Starting Minikube...${NC}"
    minikube start --memory=4096 --cpus=2 --driver=docker
else
    echo -e "${GREEN}✅ Minikube is running${NC}"
fi

# Enable necessary addons
echo -e "${YELLOW}🔧 Enabling Minikube addons...${NC}"
minikube addons enable ingress
minikube addons enable metrics-server

# Point Docker to Minikube's Docker daemon
echo -e "${YELLOW}🐳 Configuring Docker for Minikube...${NC}"
eval $(minikube docker-env)

# Build images locally in Minikube
echo -e "${YELLOW}🏗️  Building Docker images in Minikube...${NC}"

# Build Gemini service
echo "Building Gemini service..."
docker build -t geminiservice:latest src/geminiservice/

# Build other services if needed
# docker build -t frontend:latest src/frontend/

# Create namespace
echo -e "${YELLOW}📦 Creating namespace...${NC}"
kubectl apply -f kubernetes-manifests/namespace.yaml

# Create secrets from .env file
echo -e "${YELLOW}🔑 Creating secrets from .env...${NC}"
if [ -f .env ]; then
    # Read .env file and create secret
    GEMINI_API_KEY=$(grep GEMINI_API_KEY .env | cut -d '=' -f2)
    GEMINI_MODEL=$(grep GEMINI_MODEL .env | cut -d '=' -f2 | cut -d ' ' -f1)
    GEMINI_API_ENDPOINT=$(grep GEMINI_API_ENDPOINT .env | cut -d '=' -f2)
    
    kubectl create secret generic gemini-secret \
        --from-literal=api-key="$GEMINI_API_KEY" \
        --from-literal=model="$GEMINI_MODEL" \
        --from-literal=endpoint="$GEMINI_API_ENDPOINT" \
        -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    echo -e "${GREEN}✅ Secrets created from .env${NC}"
else
    echo -e "${RED}⚠️  .env file not found${NC}"
fi

# Deploy Redis
echo -e "${YELLOW}🗄️  Deploying Redis...${NC}"
kubectl apply -f kubernetes-manifests/redis.yaml

# Update Gemini deployment to use local image
echo -e "${YELLOW}📝 Creating local Gemini deployment...${NC}"
cat > kubernetes-manifests/gemini-service/deployment-local.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: geminiservice
  namespace: quanbuy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: geminiservice
  template:
    metadata:
      labels:
        app: geminiservice
    spec:
      containers:
      - name: server
        image: geminiservice:latest
        imagePullPolicy: Never  # Use local image
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: PORT
          value: "8080"
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secret
              key: api-key
        - name: GEMINI_MODEL
          valueFrom:
            secretKeyRef:
              name: gemini-secret
              key: model
        - name: GEMINI_API_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: gemini-secret
              key: endpoint
        - name: REDIS_HOST
          value: "redis-service"
        - name: REDIS_PORT
          value: "6379"
        - name: LOCAL_MODE
          value: "true"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
EOF

# Deploy Gemini service
echo -e "${YELLOW}🚀 Deploying Gemini service...${NC}"
kubectl apply -f kubernetes-manifests/gemini-service/deployment-local.yaml
kubectl apply -f kubernetes-manifests/gemini-service/service.yaml

# Deploy a simple nginx to serve the UI
echo -e "${YELLOW}🌐 Deploying UI server...${NC}"
cat > kubernetes-manifests/ui-deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ui-server
  namespace: quanbuy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ui-server
  template:
    metadata:
      labels:
        app: ui-server
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: html
          mountPath: /usr/share/nginx/html
      volumes:
      - name: html
        configMap:
          name: ui-html
---
apiVersion: v1
kind: Service
metadata:
  name: ui-server
  namespace: quanbuy
spec:
  type: NodePort
  selector:
    app: ui-server
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
EOF

# Create ConfigMap with HTML
kubectl create configmap ui-html --from-file=quanbuy.html -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy UI
kubectl apply -f kubernetes-manifests/ui-deployment.yaml

# Wait for deployments
echo -e "${YELLOW}⏳ Waiting for deployments to be ready...${NC}"
kubectl wait --for=condition=available --timeout=120s \
    deployment/geminiservice \
    deployment/redis \
    deployment/ui-server \
    -n $NAMESPACE

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Port forward for easier access
echo -e "${YELLOW}🔌 Setting up port forwarding...${NC}"
kubectl port-forward svc/geminiservice 8081:8080 -n $NAMESPACE &
kubectl port-forward svc/ui-server 8000:80 -n $NAMESPACE &

# Display status
echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}📱 Access Points:${NC}"
echo "  • UI: http://localhost:8000/quanbuy.html"
echo "  • UI (NodePort): http://$MINIKUBE_IP:30080/quanbuy.html"
echo "  • Gemini API: http://localhost:8081"
echo "  • API Docs: http://localhost:8081/docs"
echo ""
echo -e "${BLUE}🧪 Test the Gemini Service:${NC}"
echo ""
echo "Mystery Search:"
echo "  curl -X POST http://localhost:8081/mystery-search \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"user_id\": \"test123\", \"search_history\": [\"vintage\", \"bohemian\"]}'"
echo ""
echo -e "${YELLOW}📊 Useful commands:${NC}"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl logs -f deployment/geminiservice -n $NAMESPACE"
echo "  minikube dashboard"
echo ""
echo -e "${YELLOW}🛑 To clean up:${NC}"
echo "  kubectl delete namespace $NAMESPACE"
echo "  minikube stop"
