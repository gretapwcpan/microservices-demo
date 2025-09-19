<!-- <p align="center">
<img src="/src/frontend/static/icons/Hipster_HeroLogoMaroon.svg" width="300" alt="Online Boutique" />
</p> -->
![Continuous Integration](https://github.com/GoogleCloudPlatform/microservices-demo/workflows/Continuous%20Integration%20-%20Main/Release/badge.svg)

**Online Boutique** is a cloud-first microservices demo application.  The application is a
web-based e-commerce app where users can browse items, add them to the cart, and purchase them.

Google uses this application to demonstrate how developers can modernize enterprise applications using Google Cloud products, including: [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine), [Cloud Service Mesh (CSM)](https://cloud.google.com/service-mesh), [gRPC](https://grpc.io/), [Cloud Operations](https://cloud.google.com/products/operations), [Spanner](https://cloud.google.com/spanner), [Memorystore](https://cloud.google.com/memorystore), [AlloyDB](https://cloud.google.com/alloydb), and [Gemini](https://ai.google.dev/). This application works on any Kubernetes cluster.

If you’re using this demo, please **★Star** this repository to show your interest!

**Note to Googlers:** Please fill out the form at [go/microservices-demo](http://go/microservices-demo).

## Architecture

**Online Boutique** is composed of 11 microservices written in different
languages that talk to each other over gRPC.

[![Architecture of
microservices](/docs/img/architecture-diagram.png)](/docs/img/architecture-diagram.png)

Find **Protocol Buffers Descriptions** at the [`./protos` directory](/protos).

| Service                                              | Language      | Description                                                                                                                       |
| ---------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| [frontend](/src/frontend)                           | Go            | Exposes an HTTP server to serve the website. Does not require signup/login and generates session IDs for all users automatically. |
| [cartservice](/src/cartservice)                     | C#            | Stores the items in the user's shopping cart in Redis and retrieves it.                                                           |
| [productcatalogservice](/src/productcatalogservice) | Go            | Provides the list of products from a JSON file and ability to search products and get individual products.                        |
| [currencyservice](/src/currencyservice)             | Node.js       | Converts one money amount to another currency. Uses real values fetched from European Central Bank. It's the highest QPS service. |
| [paymentservice](/src/paymentservice)               | Node.js       | Charges the given credit card info (mock) with the given amount and returns a transaction ID.                                     |
| [shippingservice](/src/shippingservice)             | Go            | Gives shipping cost estimates based on the shopping cart. Ships items to the given address (mock)                                 |
| [emailservice](/src/emailservice)                   | Python        | Sends users an order confirmation email (mock).                                                                                   |
| [checkoutservice](/src/checkoutservice)             | Go            | Retrieves user cart, prepares order and orchestrates the payment, shipping and the email notification.                            |
| [recommendationservice](/src/recommendationservice) | Python        | Recommends other products based on what's given in the cart.                                                                      |
| [adservice](/src/adservice)                         | Java          | Provides text ads based on given context words.                                                                                   |
| [loadgenerator](/src/loadgenerator)                 | Python/Locust | Continuously sends requests imitating realistic user shopping flows to the frontend.                                              |

## Screenshots

| Home Page                                                                                                         | Checkout Screen                                                                                                    |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| [![Screenshot of store homepage](/docs/img/online-boutique-frontend-1.png)](/docs/img/online-boutique-frontend-1.png) | [![Screenshot of checkout screen](/docs/img/online-boutique-frontend-2.png)](/docs/img/online-boutique-frontend-2.png) |

## Quickstart (GKE)

1. Ensure you have the following requirements:
   - [Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project).
   - Shell environment with `gcloud`, `git`, and `kubectl`.

2. Clone the latest major version.

   ```sh
   git clone --depth 1 --branch v0 https://github.com/GoogleCloudPlatform/microservices-demo.git
   cd microservices-demo/
   ```

   The `--depth 1` argument skips downloading git history.

3. Set the Google Cloud project and region and ensure the Google Kubernetes Engine API is enabled.

   ```sh
   export PROJECT_ID=<PROJECT_ID>
   export REGION=us-central1
   gcloud services enable container.googleapis.com \
     --project=${PROJECT_ID}
   ```

   Substitute `<PROJECT_ID>` with the ID of your Google Cloud project.

4. Create a GKE cluster and get the credentials for it.

   ```sh
   gcloud container clusters create-auto online-boutique \
     --project=${PROJECT_ID} --region=${REGION}
   ```

   Creating the cluster may take a few minutes.

5. Deploy Online Boutique to the cluster.

   ```sh
   kubectl apply -f ./release/kubernetes-manifests.yaml
   ```

6. Wait for the pods to be ready.

   ```sh
   kubectl get pods
   ```

   After a few minutes, you should see the Pods in a `Running` state:

   ```
   NAME                                     READY   STATUS    RESTARTS   AGE
   adservice-76bdd69666-ckc5j               1/1     Running   0          2m58s
   cartservice-66d497c6b7-dp5jr             1/1     Running   0          2m59s
   checkoutservice-666c784bd6-4jd22         1/1     Running   0          3m1s
   currencyservice-5d5d496984-4jmd7         1/1     Running   0          2m59s
   emailservice-667457d9d6-75jcq            1/1     Running   0          3m2s
   frontend-6b8d69b9fb-wjqdg                1/1     Running   0          3m1s
   loadgenerator-665b5cd444-gwqdq           1/1     Running   0          3m
   paymentservice-68596d6dd6-bf6bv          1/1     Running   0          3m
   productcatalogservice-557d474574-888kr   1/1     Running   0          3m
   recommendationservice-69c56b74d4-7z8r5   1/1     Running   0          3m1s
   redis-cart-5f59546cdd-5jnqf              1/1     Running   0          2m58s
   shippingservice-6ccc89f8fd-v686r         1/1     Running   0          2m58s
   ```

7. Access the web frontend in a browser using the frontend's external IP.

   ```sh
   kubectl get service frontend-external | awk '{print $4}'
   ```

   Visit `http://EXTERNAL_IP` in a web browser to access your instance of Online Boutique.

8. Congrats! You've deployed the default Online Boutique. To deploy a different variation of Online Boutique (e.g., with Google Cloud Operations tracing, Istio, etc.), see [Deploy Online Boutique variations with Kustomize](#deploy-online-boutique-variations-with-kustomize).

9. Once you are done with it, delete the GKE cluster.

   ```sh
   gcloud container clusters delete online-boutique \
     --project=${PROJECT_ID} --region=${REGION}
   ```

   Deleting the cluster may take a few minutes.

## Local Development with Kind

[Kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker) provides a lightweight way to run Kubernetes clusters locally for development and testing.

### Prerequisites

1. Install Docker Desktop or Docker Engine
2. Install Kind:
   ```sh
   # On macOS with Homebrew
   brew install kind
   
   # On Linux/macOS with curl
   curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-$(uname)-amd64
   chmod +x ./kind
   sudo mv ./kind /usr/local/bin/kind
   ```

3. Install kubectl if not already installed

### Quick Start with Kind

1. **Create a Kind cluster:**
   ```sh
   kind create cluster --name microservices-demo
   ```

2. **Verify cluster is running:**
   ```sh
   kubectl cluster-info --context kind-microservices-demo
   ```

3. **Deploy Online Boutique:**
   ```sh
   kubectl apply -f ./release/kubernetes-manifests.yaml
   ```

4. **Wait for all pods to be ready:**
   ```sh
   kubectl wait --for=condition=ready pods --all -n default --timeout=300s
   ```

5. **Access the application:**
   ```sh
   kubectl port-forward service/frontend 8080:80
   ```
   Visit http://localhost:8080 in your browser.
   
   **Note**: If port 8080 is already in use, try a different port:
   ```sh
   kubectl port-forward service/frontend 8090:80
   ```
   Then visit http://localhost:8090 instead.

6. **Cleanup:**
   ```sh
   kind delete cluster --name microservices-demo
   ```

### Testing AI-Enhanced Components Locally

The project includes AI-powered components that enhance the shopping experience using Google's Gemini AI.

#### Components Overview

- **MCP Server**: REST API gateway that translates HTTP requests to gRPC calls for microservices
- **Shopping Agent**: AI-powered chat interface using Google Gemini for natural language shopping assistance

#### Quick Setup and Testing

1. **Deploy the Shopping Agent with Gemini AI:**
   ```sh
   # This script builds, loads, and deploys the Shopping Agent
   ./deploy-gemini-agent.sh
   ```

2. **Configure Google AI API Key:**
   
   Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey) and update `google-ai-secret.yaml`:
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: google-ai-secrets
   type: Opaque
   stringData:
     api-key: "YOUR_ACTUAL_API_KEY_HERE"  # Replace with your key
   ```
   
   Apply the secret:
   ```sh
   kubectl apply -f google-ai-secret.yaml
   ```

3. **Run the E2E Test Suite:**
   ```sh
   # Comprehensive test of the Shopping Agent
   ./test-shopping-agent.sh
   ```
   
   This test script will:
   - Verify all services are running
   - Test Shopping Agent health
   - Run various chat scenarios (greeting, browsing, searching, cart operations)
   - Display Gemini AI responses
   - Check MCP Server connectivity

#### Manual Testing

For manual interaction with the Shopping Agent:

```sh
# 1. Port-forward the service
kubectl port-forward service/shopping-agent 8084:8081

# 2. Test various scenarios
# Health check
curl http://localhost:8084/health | python3 -m json.tool

# Natural language chat
curl -X POST http://localhost:8084/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "Show me some vintage cameras"}' \
  | python3 -m json.tool

# Browse products
curl -X POST http://localhost:8084/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "What products do you have?"}' \
  | python3 -m json.tool

# Cart operations
curl -X POST http://localhost:8084/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "What is in my cart?"}' \
  | python3 -m json.tool
```

#### Testing Scenarios

**With Gemini API Key:**
- Natural language understanding
- Context-aware responses
- Intelligent product recommendations
- Complex query handling

**Without API Key (Demo Mode):**
- Basic keyword matching for product searches
- Limited to predefined responses

#### Troubleshooting

1. **Pods not starting:**
   ```sh
   kubectl describe pod <pod-name>
   kubectl logs <pod-name>
   ```

2. **Image not found:**
   Ensure images are loaded into Kind:
   ```sh
   docker exec -it microservices-demo-control-plane crictl images | grep -E "mcp-server|shopping-agent"
   ```

3. **Port-forward issues:**
   Kill existing port-forwards:
   ```sh
   pkill -f "port-forward"
   ```

4. **Resource issues:**
   If services are crashing, restart the Kind cluster:
   ```sh
   kind delete cluster --name microservices-demo
   kind create cluster --name microservices-demo
   ```

#### Clean Up AI Components

To remove only the AI components while keeping the base application:
```sh
kubectl delete -f kubernetes-manifests/mcp-server.yaml
kubectl delete -f kubernetes-manifests/shopping-agent.yaml
kubectl delete secret google-ai-secrets
```

## Additional deployment options

- **Terraform**: [See these instructions](/terraform) to learn how to deploy Online Boutique using [Terraform](https://www.terraform.io/intro).
- **Istio / Cloud Service Mesh**: [See these instructions](/kustomize/components/service-mesh-istio/README.md) to deploy Online Boutique alongside an Istio-backed service mesh.
- **Non-GKE clusters (Minikube, Kind, etc)**: See the [Development guide](/docs/development-guide.md) to learn how you can deploy Online Boutique on non-GKE clusters.

## Documentation

- [Development](/docs/development-guide.md) to learn how to run and develop this app locally.

## Demos featuring Online Boutique

- [Platform Engineering in action: Deploy the Online Boutique sample apps with Score and Humanitec](https://medium.com/p/d99101001e69)
- [The new Kubernetes Gateway API with Istio and Anthos Service Mesh (ASM)](https://medium.com/p/9d64c7009cd)
- [Use Azure Redis Cache with the Online Boutique sample on AKS](https://medium.com/p/981bd98b53f8)
- [Sail Sharp, 8 tips to optimize and secure your .NET containers for Kubernetes](https://medium.com/p/c68ba253844a)
- [Deploy multi-region application with Anthos and Google cloud Spanner](https://medium.com/google-cloud/a2ea3493ed0)
- [Use Google Cloud Memorystore (Redis) with the Online Boutique sample on GKE](https://medium.com/p/82f7879a900d)
- [Use Helm to simplify the deployment of Online Boutique, with a Service Mesh, GitOps, and more!](https://medium.com/p/246119e46d53)
- [How to reduce microservices complexity with Apigee and Anthos Service Mesh](https://cloud.google.com/blog/products/application-modernization/api-management-and-service-mesh-go-together)
- [gRPC health probes with Kubernetes 1.24+](https://medium.com/p/b5bd26253a4c)
- [Use Google Cloud Spanner with the Online Boutique sample](https://medium.com/p/f7248e077339)
- [Seamlessly encrypt traffic from any apps in your Mesh to Memorystore (redis)](https://medium.com/google-cloud/64b71969318d)
- [Strengthen your app's security with Cloud Service Mesh and Anthos Config Management](https://cloud.google.com/service-mesh/docs/strengthen-app-security)
- [From edge to mesh: Exposing service mesh applications through GKE Ingress](https://cloud.google.com/architecture/exposing-service-mesh-apps-through-gke-ingress)
- [Take the first step toward SRE with Cloud Operations Sandbox](https://cloud.google.com/blog/products/operations/on-the-road-to-sre-with-cloud-operations-sandbox)
- [Deploying the Online Boutique sample application on Cloud Service Mesh](https://cloud.google.com/service-mesh/docs/onlineboutique-install-kpt)
- [Anthos Service Mesh Workshop: Lab Guide](https://codelabs.developers.google.com/codelabs/anthos-service-mesh-workshop)
- [KubeCon EU 2019 - Reinventing Networking: A Deep Dive into Istio's Multicluster Gateways - Steve Dake, Independent](https://youtu.be/-t2BfT59zJA?t=982)
- Google Cloud Next'18 SF
  - [Day 1 Keynote](https://youtu.be/vJ9OaAqfxo4?t=2416) showing GKE On-Prem
  - [Day 3 Keynote](https://youtu.be/JQPOPV_VH5w?t=815) showing Stackdriver
    APM (Tracing, Code Search, Profiler, Google Cloud Build)
  - [Introduction to Service Management with Istio](https://www.youtube.com/watch?v=wCJrdKdD6UM&feature=youtu.be&t=586)
- [Google Cloud Next'18 London – Keynote](https://youtu.be/nIq2pkNcfEI?t=3071)
  showing Stackdriver Incident Response Management
- [Microservices demo showcasing Go Micro](https://github.com/go-micro/demo)
