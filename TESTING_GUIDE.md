# Shopping Agent Testing Guide

## Quick Start

### 1. Deploy the Shopping Agent
```bash
./deploy-gemini-agent.sh
```

### 2. Configure API Key
Edit `google-ai-secret.yaml` with your API key from [Google AI Studio](https://makersuite.google.com/app/apikey):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: google-ai-secrets
type: Opaque
stringData:
  api-key: "YOUR_ACTUAL_API_KEY_HERE"
```

Apply it:
```bash
kubectl apply -f google-ai-secret.yaml
```

### 3. Run E2E Tests
```bash
./test-shopping-agent.sh
```

## Test Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy-gemini-agent.sh` | Build, load, and deploy Shopping Agent with Gemini AI | `./deploy-gemini-agent.sh` |
| `test-shopping-agent.sh` | Run comprehensive E2E tests | `./test-shopping-agent.sh` |

## Manual Testing

### Port-forward and test manually:
```bash
# Setup port-forward
kubectl port-forward service/shopping-agent 8084:8081

# Test chat
curl -X POST http://localhost:8084/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Show me some products"}' \
  | python3 -m json.tool
```

## Test Scenarios

The `test-shopping-agent.sh` script tests:
- ✅ Health check
- ✅ Natural language greetings
- ✅ Product browsing
- ✅ Product search (e.g., "vintage camera")
- ✅ Cart operations
- ✅ MCP Server connectivity

## Troubleshooting

### Check logs:
```bash
kubectl logs -f deployment/shopping-agent
```

### Verify API key:
```bash
POD=$(kubectl get pods -l app=shopping-agent -o jsonpath='{.items[0].metadata.name}')
kubectl exec $POD -- printenv | grep GOOGLE_AI_API_KEY
```

### Test API key in pod:
```bash
# Check if the API key is properly set in the pod
kubectl get secret google-ai-secrets -o jsonpath='{.data.api-key}' | base64 -d
```

## Clean Up

Remove AI components:
```bash
kubectl delete -f kubernetes-manifests/shopping-agent.yaml
kubectl delete -f kubernetes-manifests/mcp-server.yaml
kubectl delete secret google-ai-secrets
