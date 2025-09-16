#!/bin/bash

echo "=== Deploying Shopping Agent with Gemini AI ==="
echo ""

# Step 1: Build the Docker image
echo "Step 1: Building Docker image shopping-agent:v9..."
docker build -t shopping-agent:v9 -f src/agentic-ai/agents/shopping-agent/Dockerfile .
if [ $? -ne 0 ]; then
    echo "Error: Docker build failed"
    exit 1
fi
echo "✓ Docker image built successfully"
echo ""

# Step 2: Load image into Kind
echo "Step 2: Loading image into Kind cluster..."
kind load docker-image shopping-agent:v9 --name microservices-demo
if [ $? -ne 0 ]; then
    echo "Error: Failed to load image into Kind"
    exit 1
fi
echo "✓ Image loaded into Kind"
echo ""

# Step 3: Delete existing deployment
echo "Step 3: Deleting existing deployment..."
kubectl delete deployment shopping-agent 2>/dev/null
sleep 2
echo "✓ Old deployment deleted"
echo ""

# Step 4: Apply new deployment
echo "Step 4: Applying new deployment..."
kubectl apply -f kubernetes-manifests/shopping-agent.yaml
if [ $? -ne 0 ]; then
    echo "Error: Failed to apply deployment"
    exit 1
fi
echo "✓ New deployment applied"
echo ""

# Step 5: Wait for pods to be ready
echo "Step 5: Waiting for pods to be ready..."
for i in {1..30}; do
    READY=$(kubectl get pods -l app=shopping-agent -o jsonpath='{.items[*].status.containerStatuses[*].ready}' | grep -o "true" | wc -l)
    TOTAL=$(kubectl get pods -l app=shopping-agent --no-headers | wc -l)
    
    if [ "$READY" -eq "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
        echo "✓ All $TOTAL pods are ready!"
        break
    fi
    
    echo "Waiting... ($READY/$TOTAL pods ready)"
    sleep 2
done
echo ""

# Step 6: Show pod status
echo "Step 6: Current pod status:"
kubectl get pods -l app=shopping-agent
echo ""

# Step 7: Check logs
echo "Step 7: Checking logs from first pod:"
POD=$(kubectl get pods -l app=shopping-agent -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD --tail=5
echo ""

# Step 8: Test the service
echo "Step 8: Testing the service..."
pkill -f "port-forward.*808[0-9]" 2>/dev/null
kubectl port-forward service/shopping-agent 8086:8081 > /dev/null 2>&1 &
PF_PID=$!
sleep 3

echo "Health check:"
curl -s http://localhost:8086/health | python3 -m json.tool
echo ""

echo "Chat test (using Gemini AI):"
curl -s -X POST http://localhost:8086/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Hello! I want to buy something nice"}' \
  | python3 -m json.tool

kill $PF_PID 2>/dev/null

echo ""
echo "=== Deployment Complete ==="
