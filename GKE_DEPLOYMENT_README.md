# quanBuy GKE Deployment Guide

## 🚀 Architecture Overview

quanBuy is deployed on Google Kubernetes Engine (GKE) with the following architecture:

### Core Services
- **Frontend Service** (Go) - Serves the artistic UI
- **Gemini Service** (Python) - AI-powered features using Google's Gemini
- **Currency Service** (Node.js) - Currency conversion
- **Checkout Service** (Go) - Order processing
- **QuanBuy Service** (Python) - Core marketplace logic

### Infrastructure Components
- **GKE Standard** - Cost-optimized Kubernetes cluster
- **Spot VMs** - 60-91% cost savings for non-critical workloads
- **Cloud Load Balancer** - HTTPS ingress
- **Cloud CDN** - Global content delivery
- **Firestore** - NoSQL database
- **Redis** - Caching & sessions
- **Cloud Pub/Sub** - Event streaming
- **Gemini API** - AI capabilities

## 📋 Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Tools installed:**
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   
   # Install kubectl
   gcloud components install kubectl
   
   # Install Docker
   # Visit https://docs.docker.com/get-docker/
   ```

3. **APIs to enable:**
   - Kubernetes Engine API
   - Compute Engine API
   - Cloud Firestore API
   - Cloud Pub/Sub API
   - Vertex AI API

## 🔧 Setup Instructions

### 1. Configure GCP Project

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"

# Authenticate
gcloud auth login
gcloud config set project $GCP_PROJECT_ID
```

### 2. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Save it securely

### 3. Create Service Account

```bash
# Create service account for the application
gcloud iam service-accounts create quanbuy-sa \
    --display-name="quanBuy Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:quanbuy-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:quanbuy-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

# Download key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=quanbuy-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

### 4. Deploy to GKE

```bash
# Make deployment script executable
chmod +x deploy-to-gke.sh

# Run deployment
./deploy-to-gke.sh
```

### 5. Create Secrets

```bash
# Create Gemini API secret
kubectl create secret generic gemini-secret \
    --from-literal=api-key="YOUR_GEMINI_API_KEY" \
    -n quanbuy

# Create GCP service account secret
kubectl create secret generic gcp-service-account-key \
    --from-file=key.json=service-account-key.json \
    -n quanbuy
```

### 6. Reserve Static IP

```bash
# Reserve a global static IP
gcloud compute addresses create quanbuy-ip --global

# Get the IP address
gcloud compute addresses describe quanbuy-ip --global
```

### 7. Configure DNS

Point your domain to the static IP:
- Add an A record for `quanbuy.yourdomain.com` → Static IP
- Add an A record for `www.quanbuy.yourdomain.com` → Static IP

## 🎮 Viral Features

### AI-Powered Features (via Gemini)

1. **Mystery Search** 
   - Endpoint: `/api/gemini/mystery-search`
   - AI generates surprising product discoveries

2. **Oracle Mode**
   - Endpoint: `/api/gemini/oracle-search`
   - Search by feelings/moods

3. **Discovery Stories**
   - Endpoint: `/api/gemini/discovery-story`
   - AI-generated narratives of search journeys

4. **Search DNA**
   - Endpoint: `/api/gemini/search-dna`
   - Visual representation of search patterns

### Addictive Mechanics

- **Search Streaks** - Daily engagement tracking
- **Collaborative Rooms** - Real-time group searching
- **Gamification** - Levels, achievements, challenges
- **Social Sharing** - One-click story sharing

## 📊 Monitoring

### View Application Status

```bash
# Check pods
kubectl get pods -n quanbuy

# Check services
kubectl get svc -n quanbuy

# Check ingress
kubectl get ingress -n quanbuy

# View logs
kubectl logs -f deployment/geminiservice -n quanbuy
kubectl logs -f deployment/frontend -n quanbuy
```

### Google Cloud Monitoring

1. Go to [Cloud Console](https://console.cloud.google.com)
2. Navigate to Kubernetes Engine → Workloads
3. View metrics, logs, and traces

## 🧪 Testing

### Local Testing

```bash
# Port forward to test locally
kubectl port-forward svc/frontend 8080:80 -n quanbuy

# Access at http://localhost:8080
```

### Test Gemini Service

```bash
# Port forward Gemini service
kubectl port-forward svc/geminiservice 8081:8080 -n quanbuy

# Test mystery search
curl -X POST http://localhost:8081/mystery-search \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "search_history": ["vintage", "bohemian"]}'
```

## 🔄 Updating Services

### Update Gemini Service

```bash
# Rebuild and push
docker build -t gcr.io/$GCP_PROJECT_ID/geminiservice:latest src/geminiservice/
docker push gcr.io/$GCP_PROJECT_ID/geminiservice:latest

# Restart deployment
kubectl rollout restart deployment/geminiservice -n quanbuy
```

### Update Frontend

```bash
# After modifying frontend code
docker build -t gcr.io/$GCP_PROJECT_ID/frontend:latest src/frontend/
docker push gcr.io/$GCP_PROJECT_ID/frontend:latest
kubectl rollout restart deployment/frontend -n quanbuy
```

## 💰 Cost Optimization

### GKE Standard vs Autopilot
- **GKE Standard**: ~40-50% cheaper than Autopilot
- **Node configuration**: e2-medium (2 vCPU, 4GB RAM)
- **Auto-scaling**: 1-3 nodes based on load
- **Disk**: 30GB standard persistent disk

### Spot VM Node Pool
- **Separate pool** for non-critical workloads
- **60-91% cheaper** than regular VMs
- **e2-small instances** (2 vCPU, 2GB RAM)
- **Auto-scales**: 0-2 nodes as needed

### Cost Breakdown (Estimated Monthly)
```
GKE Standard (3 e2-medium nodes):     ~$75-100
Spot Pool (2 e2-small spot):          ~$10-15
Load Balancer:                        ~$18
Cloud CDN:                            ~$0-20 (based on usage)
Firestore (free tier):                $0
Redis (in-cluster):                   $0
Total:                                ~$103-153/month
```

### Additional Savings Tips
1. **Use Committed Use Discounts**: Save 37-55% with 1-year commitment
2. **Regional cluster**: Cheaper than multi-zone
3. **Firestore free tier**: 1GB storage, 50K reads/day
4. **Cloud CDN caching**: Reduces egress costs
5. **Spot VMs for batch jobs**: Up to 91% savings
6. **Monitor unused resources**: Delete idle services

## 🚨 Troubleshooting

### Common Issues

1. **Pods not starting**
   ```bash
   kubectl describe pod POD_NAME -n quanbuy
   ```

2. **Ingress not getting IP**
   - Wait 5-10 minutes for provisioning
   - Check: `kubectl describe ingress quanbuy-ingress -n quanbuy`

3. **Gemini API errors**
   - Verify API key is correct
   - Check quotas in Google AI Studio

4. **Redis connection issues**
   ```bash
   kubectl exec -it deployment/redis -n quanbuy -- redis-cli ping
   ```

## 📚 Additional Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Gemini API Docs](https://ai.google.dev/docs)
- [Firestore Guide](https://cloud.google.com/firestore/docs)
- [Cloud CDN Setup](https://cloud.google.com/cdn/docs)

## 🤝 Support

For issues or questions:
1. Check the logs: `kubectl logs -f deployment/SERVICE_NAME -n quanbuy`
2. Review Cloud Console error reporting
3. Check service health: `curl http://SERVICE_URL/health`

## 🎯 Next Steps

1. **Enable monitoring** - Set up alerts and dashboards
2. **Configure CI/CD** - Use Cloud Build for automated deployments
3. **Add custom domain** - Configure SSL certificates
4. **Scale services** - Adjust HPA settings based on traffic
5. **Implement backup** - Set up Firestore backups

---

**Built with ❤️ for mindful discovery**
