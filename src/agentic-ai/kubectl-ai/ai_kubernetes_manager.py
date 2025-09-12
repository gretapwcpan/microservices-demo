#!/usr/bin/env python3
"""
AI-Powered Kubernetes Management System
Integrates with kubectl-ai for intelligent cluster operations
"""

import asyncio
import json
import logging
import subprocess
import time
import uuid
from typing import Dict, List, Optional, Any, Union
import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KubernetesAIManager:
    """AI-powered Kubernetes management system"""
    
    def __init__(self):
        self.setup_kubernetes_client()
        self.setup_gemini()
        self.operation_history: List[Dict[str, Any]] = []
        
    def setup_kubernetes_client(self):
        """Initialize Kubernetes client"""
        try:
            # Try in-cluster config first, then local config
            try:
                config.load_incluster_config()
                logger.info("Using in-cluster Kubernetes configuration")
            except:
                config.load_kube_config()
                logger.info("Using local Kubernetes configuration")
            
            self.k8s_apps_v1 = client.AppsV1Api()
            self.k8s_core_v1 = client.CoreV1Api()
            self.k8s_autoscaling_v1 = client.AutoscalingV1Api()
            self.k8s_networking_v1 = client.NetworkingV1Api()
            
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise
    
    def setup_gemini(self):
        """Initialize Gemini for AI operations"""
        api_key = os.getenv('GOOGLE_AI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
        
        self.gemini_pro = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.1  # Low temperature for precise operations
        )
    
    async def process_natural_language_command(self, command: str, namespace: str = "agentic-ai") -> Dict[str, Any]:
        """Process natural language command and execute appropriate Kubernetes operations"""
        
        try:
            # Analyze the command using Gemini
            analysis = await self.analyze_command_intent(command, namespace)
            
            # Execute the operation
            if analysis["operation_type"] == "scale":
                result = await self.handle_scaling_operation(analysis, namespace)
            elif analysis["operation_type"] == "troubleshoot":
                result = await self.handle_troubleshooting_operation(analysis, namespace)
            elif analysis["operation_type"] == "optimize":
                result = await self.handle_optimization_operation(analysis, namespace)
            elif analysis["operation_type"] == "monitor":
                result = await self.handle_monitoring_operation(analysis, namespace)
            elif analysis["operation_type"] == "deploy":
                result = await self.handle_deployment_operation(analysis, namespace)
            else:
                result = await self.handle_general_operation(analysis, namespace)
            
            # Record operation
            operation_record = {
                "id": str(uuid.uuid4()),
                "timestamp": time.time(),
                "command": command,
                "analysis": analysis,
                "result": result,
                "namespace": namespace
            }
            self.operation_history.append(operation_record)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing command '{command}': {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def analyze_command_intent(self, command: str, namespace: str) -> Dict[str, Any]:
        """Analyze natural language command to determine intent and parameters"""
        
        # Get current cluster state for context
        cluster_context = await self.get_cluster_context(namespace)
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are an expert Kubernetes administrator with deep knowledge of cluster operations.
            
            Analyze the user's natural language command and extract:
            1. Operation type (scale, troubleshoot, optimize, monitor, deploy, info, other)
            2. Target resources (deployments, services, pods, etc.)
            3. Parameters and values
            4. Intent and urgency
            5. Safety considerations
            
            Return a structured JSON response:
            {{
                "operation_type": "scale|troubleshoot|optimize|monitor|deploy|info|other",
                "target_resources": [
                    {{
                        "type": "deployment|service|pod|node",
                        "name": "resource_name",
                        "namespace": "namespace"
                    }}
                ],
                "parameters": {{
                    "replicas": int,
                    "cpu_limit": "string",
                    "memory_limit": "string",
                    "timeout": int,
                    "force": boolean
                }},
                "intent": "string description",
                "urgency": "low|medium|high|critical",
                "safety_level": "safe|caution|risky",
                "estimated_impact": "string description",
                "prerequisites": ["check1", "check2"],
                "kubectl_commands": ["cmd1", "cmd2"]
            }}
            """),
            ("human", f"""
            Command: {command}
            Namespace: {namespace}
            Current Cluster State: {json.dumps(cluster_context, indent=2)}
            
            Please analyze this command and provide the structured response.
            """)
        ])
        
        try:
            response = await self.gemini_pro.ainvoke(analysis_prompt.format_messages())
            response_text = response.content
            
            # Extract JSON from response
            if "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                analysis = json.loads(json_str)
                return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing command: {e}")
        
        # Fallback analysis
        return {
            "operation_type": "other",
            "target_resources": [],
            "parameters": {},
            "intent": command,
            "urgency": "medium",
            "safety_level": "caution",
            "estimated_impact": "Unknown impact",
            "prerequisites": [],
            "kubectl_commands": []
        }
    
    async def get_cluster_context(self, namespace: str) -> Dict[str, Any]:
        """Get current cluster state for context"""
        
        try:
            context = {
                "deployments": [],
                "services": [],
                "pods": [],
                "resource_usage": {},
                "events": []
            }
            
            # Get deployments
            deployments = self.k8s_apps_v1.list_namespaced_deployment(namespace)
            for deployment in deployments.items:
                context["deployments"].append({
                    "name": deployment.metadata.name,
                    "replicas": deployment.spec.replicas,
                    "ready_replicas": deployment.status.ready_replicas or 0,
                    "available_replicas": deployment.status.available_replicas or 0
                })
            
            # Get services
            services = self.k8s_core_v1.list_namespaced_service(namespace)
            for service in services.items:
                context["services"].append({
                    "name": service.metadata.name,
                    "type": service.spec.type,
                    "ports": [{"port": port.port, "target_port": port.target_port} for port in service.spec.ports or []]
                })
            
            # Get pods
            pods = self.k8s_core_v1.list_namespaced_pod(namespace)
            for pod in pods.items:
                context["pods"].append({
                    "name": pod.metadata.name,
                    "phase": pod.status.phase,
                    "ready": sum(1 for condition in pod.status.conditions or [] if condition.type == "Ready" and condition.status == "True") > 0
                })
            
            # Get recent events
            events = self.k8s_core_v1.list_namespaced_event(namespace, limit=10)
            for event in events.items:
                context["events"].append({
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "object": f"{event.involved_object.kind}/{event.involved_object.name}"
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting cluster context: {e}")
            return {"error": str(e)}
    
    async def handle_scaling_operation(self, analysis: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """Handle scaling operations"""
        
        results = []
        
        for resource in analysis["target_resources"]:
            if resource["type"] == "deployment":
                try:
                    deployment_name = resource["name"]
                    new_replicas = analysis["parameters"].get("replicas", 1)
                    
                    # Get current deployment
                    deployment = self.k8s_apps_v1.read_namespaced_deployment(
                        name=deployment_name,
                        namespace=namespace
                    )
                    
                    current_replicas = deployment.spec.replicas
                    
                    # Update replicas
                    deployment.spec.replicas = new_replicas
                    
                    # Apply the update
                    updated_deployment = self.k8s_apps_v1.patch_namespaced_deployment(
                        name=deployment_name,
                        namespace=namespace,
                        body=deployment
                    )
                    
                    results.append({
                        "resource": f"deployment/{deployment_name}",
                        "action": "scale",
                        "previous_replicas": current_replicas,
                        "new_replicas": new_replicas,
                        "success": True
                    })
                    
                    logger.info(f"Scaled {deployment_name} from {current_replicas} to {new_replicas} replicas")
                    
                except ApiException as e:
                    results.append({
                        "resource": f"deployment/{resource['name']}",
                        "action": "scale",
                        "success": False,
                        "error": str(e)
                    })
        
        return {
            "success": all(r["success"] for r in results),
            "operation": "scaling",
            "results": results,
            "summary": f"Scaled {len([r for r in results if r['success']])} out of {len(results)} resources"
        }
    
    async def handle_troubleshooting_operation(self, analysis: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """Handle troubleshooting operations"""
        
        issues = []
        recommendations = []
        
        # Check deployment health
        deployments = self.k8s_apps_v1.list_namespaced_deployment(namespace)
        for deployment in deployments.items:
            ready_replicas = deployment.status.ready_replicas or 0
            desired_replicas = deployment.spec.replicas or 0
            
            if ready_replicas < desired_replicas:
                issues.append({
                    "type": "deployment_not_ready",
                    "resource": f"deployment/{deployment.metadata.name}",
                    "description": f"Only {ready_replicas}/{desired_replicas} replicas are ready",
                    "severity": "high" if ready_replicas == 0 else "medium"
                })
                
                recommendations.append(f"Check pod logs for {deployment.metadata.name}")
        
        # Check pod health
        pods = self.k8s_core_v1.list_namespaced_pod(namespace)
        for pod in pods.items:
            if pod.status.phase != "Running":
                issues.append({
                    "type": "pod_not_running",
                    "resource": f"pod/{pod.metadata.name}",
                    "description": f"Pod is in {pod.status.phase} state",
                    "severity": "high"
                })
                
                recommendations.append(f"Investigate pod {pod.metadata.name} - check events and logs")
        
        # Check for recent error events
        events = self.k8s_core_v1.list_namespaced_event(namespace, limit=20)
        error_events = [e for e in events.items if e.type == "Warning"]
        
        for event in error_events[-5:]:  # Last 5 warning events
            issues.append({
                "type": "warning_event",
                "resource": f"{event.involved_object.kind}/{event.involved_object.name}",
                "description": f"{event.reason}: {event.message}",
                "severity": "medium"
            })
        
        return {
            "success": True,
            "operation": "troubleshooting",
            "issues_found": len(issues),
            "issues": issues,
            "recommendations": recommendations,
            "summary": f"Found {len(issues)} issues in namespace {namespace}"
        }
    
    async def handle_optimization_operation(self, analysis: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """Handle optimization operations"""
        
        optimizations = []
        
        # Analyze resource usage and suggest optimizations
        deployments = self.k8s_apps_v1.list_namespaced_deployment(namespace)
        
        for deployment in deployments.items:
            deployment_name = deployment.metadata.name
            current_replicas = deployment.spec.replicas or 1
            
            # Get pods for this deployment
            pods = self.k8s_core_v1.list_namespaced_pod(
                namespace,
                label_selector=f"app={deployment_name}"
            )
            
            if len(pods.items) > 0:
                # Simple optimization logic
                ready_pods = sum(1 for pod in pods.items if pod.status.phase == "Running")
                
                if ready_pods > current_replicas * 1.5:
                    optimizations.append({
                        "type": "scale_down",
                        "resource": f"deployment/{deployment_name}",
                        "current_replicas": current_replicas,
                        "suggested_replicas": max(1, current_replicas - 1),
                        "reason": "Over-provisioned based on current load"
                    })
                elif ready_pods < current_replicas * 0.7:
                    optimizations.append({
                        "type": "investigate_performance",
                        "resource": f"deployment/{deployment_name}",
                        "reason": "Low ready pod ratio, investigate performance issues"
                    })
        
        return {
            "success": True,
            "operation": "optimization",
            "optimizations_found": len(optimizations),
            "optimizations": optimizations,
            "summary": f"Found {len(optimizations)} optimization opportunities"
        }
    
    async def handle_monitoring_operation(self, analysis: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """Handle monitoring operations"""
        
        metrics = {}
        
        # Get deployment metrics
        deployments = self.k8s_apps_v1.list_namespaced_deployment(namespace)
        metrics["deployments"] = {}
        
        for deployment in deployments.items:
            name = deployment.metadata.name
            metrics["deployments"][name] = {
                "desired_replicas": deployment.spec.replicas or 0,
                "ready_replicas": deployment.status.ready_replicas or 0,
                "available_replicas": deployment.status.available_replicas or 0,
                "updated_replicas": deployment.status.updated_replicas or 0
            }
        
        # Get pod metrics
        pods = self.k8s_core_v1.list_namespaced_pod(namespace)
        metrics["pods"] = {
            "total": len(pods.items),
            "running": sum(1 for pod in pods.items if pod.status.phase == "Running"),
            "pending": sum(1 for pod in pods.items if pod.status.phase == "Pending"),
            "failed": sum(1 for pod in pods.items if pod.status.phase == "Failed")
        }
        
        # Get service metrics
        services = self.k8s_core_v1.list_namespaced_service(namespace)
        metrics["services"] = {
            "total": len(services.items),
            "load_balancer": sum(1 for svc in services.items if svc.spec.type == "LoadBalancer"),
            "cluster_ip": sum(1 for svc in services.items if svc.spec.type == "ClusterIP"),
            "node_port": sum(1 for svc in services.items if svc.spec.type == "NodePort")
        }
        
        return {
            "success": True,
            "operation": "monitoring",
            "metrics": metrics,
            "timestamp": time.time(),
            "summary": f"Collected metrics for {namespace} namespace"
        }
    
    async def handle_deployment_operation(self, analysis: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """Handle deployment operations"""
        
        # This would involve more complex deployment logic
        # For now, return a placeholder
        return {
            "success": True,
            "operation": "deployment",
            "message": "Deployment operations require specific manifests",
            "analysis": analysis
        }
    
    async def handle_general_operation(self, analysis: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """Handle general operations"""
        
        # Use kubectl-ai for general operations
        kubectl_commands = analysis.get("kubectl_commands", [])
        results = []
        
        for cmd in kubectl_commands:
            try:
                # Execute kubectl command safely
                if cmd.startswith("kubectl"):
                    result = subprocess.run(
                        cmd.split(),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    results.append({
                        "command": cmd,
                        "success": result.returncode == 0,
                        "output": result.stdout,
                        "error": result.stderr
                    })
                else:
                    results.append({
                        "command": cmd,
                        "success": False,
                        "error": "Only kubectl commands are allowed"
                    })
                    
            except Exception as e:
                results.append({
                    "command": cmd,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": any(r["success"] for r in results),
            "operation": "general",
            "command_results": results,
            "analysis": analysis
        }
    
    async def get_operation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent operation history"""
        return self.operation_history[-limit:]

# FastAPI Application
app = FastAPI(title="AI Kubernetes Manager", version="1.0.0")

# Global manager instance
k8s_ai_manager = KubernetesAIManager()

class KubernetesCommand(BaseModel):
    """Request model for Kubernetes commands"""
    command: str
    namespace: str = "agentic-ai"

@app.post("/kubectl-ai")
async def execute_kubectl_ai_command(request: KubernetesCommand):
    """Execute natural language Kubernetes command"""
    try:
        result = await k8s_ai_manager.process_natural_language_command(
            request.command,
            request.namespace
        )
        return result
    except Exception as e:
        logger.error(f"Error executing kubectl-ai command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cluster-status")
async def get_cluster_status(namespace: str = "agentic-ai"):
    """Get cluster status"""
    try:
        context = await k8s_ai_manager.get_cluster_context(namespace)
        return context
    except Exception as e:
        logger.error(f"Error getting cluster status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/operation-history")
async def get_operation_history(limit: int = 10):
    """Get operation history"""
    history = await k8s_ai_manager.get_operation_history(limit)
    return {"history": history}

@app.post("/scale")
async def scale_deployment(
    deployment: str,
    replicas: int,
    namespace: str = "agentic-ai"
):
    """Scale a deployment"""
    command = f"Scale {deployment} to {replicas} replicas"
    result = await k8s_ai_manager.process_natural_language_command(command, namespace)
    return result

@app.post("/troubleshoot")
async def troubleshoot_namespace(namespace: str = "agentic-ai"):
    """Troubleshoot namespace issues"""
    command = f"Troubleshoot issues in {namespace} namespace"
    result = await k8s_ai_manager.process_natural_language_command(command, namespace)
    return result

@app.post("/optimize")
async def optimize_resources(namespace: str = "agentic-ai"):
    """Optimize resource allocation"""
    command = f"Optimize resource allocation in {namespace} namespace"
    result = await k8s_ai_manager.process_natural_language_command(command, namespace)
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-kubernetes-manager",
        "kubernetes_client": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)