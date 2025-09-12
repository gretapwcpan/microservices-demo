#!/usr/bin/env python3
"""
Multi-Agent Orchestrator for Online Boutique
Coordinates complex workflows across multiple AI agents using A2A protocol
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a2a_protocol.protocol import (
    A2AProtocolEngine, A2AWorkflowEngine, A2AMessage, MessageType, 
    AgentCapability, AgentInterface
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowRequest(BaseModel):
    """Request model for workflow execution"""
    workflow_type: str
    user_id: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class WorkflowResponse(BaseModel):
    """Response model for workflow execution"""
    workflow_id: str
    status: str
    results: Dict[str, Any]
    duration: float
    steps_completed: int
    total_steps: int

class MultiAgentOrchestrator(AgentInterface):
    """Orchestrator that coordinates multiple AI agents for complex workflows"""
    
    def __init__(self):
        self.agent_id = "multi-agent-orchestrator"
        self.a2a_engine = A2AProtocolEngine(self.agent_id)
        self.workflow_engine = A2AWorkflowEngine(self.agent_id)
        self.workflow_templates = self.initialize_workflow_templates()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Register A2A message handlers
        self.setup_message_handlers()
    
    def initialize_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predefined workflow templates"""
        return {
            "intelligent_shopping": {
                "name": "Intelligent Shopping Workflow",
                "description": "Complete shopping assistance with personalization and optimization",
                "steps": [
                    {
                        "name": "analyze_intent",
                        "agent": "gemini-shopping-agent",
                        "action": "analyze_shopping_intent",
                        "parameters": {}
                    },
                    {
                        "name": "search_products",
                        "agent": "gemini-shopping-agent", 
                        "action": "search_products",
                        "parameters": {}
                    },
                    {
                        "name": "optimize_pricing",
                        "agent": "pricing-optimizer-agent",
                        "action": "optimize_product_pricing",
                        "parameters": {}
                    },
                    {
                        "name": "personalize_recommendations",
                        "agent": "recommendation-agent",
                        "action": "generate_personalized_recommendations",
                        "parameters": {}
                    },
                    {
                        "name": "optimize_journey",
                        "agent": "journey-orchestrator-agent",
                        "action": "optimize_customer_experience",
                        "parameters": {}
                    }
                ]
            },
            "smart_checkout": {
                "name": "Smart Checkout Workflow",
                "description": "Intelligent checkout process with fraud detection and optimization",
                "steps": [
                    {
                        "name": "validate_cart",
                        "agent": "gemini-shopping-agent",
                        "action": "validate_cart_contents",
                        "parameters": {}
                    },
                    {
                        "name": "fraud_analysis",
                        "agent": "security-guardian-agent",
                        "action": "analyze_transaction_risk",
                        "parameters": {}
                    },
                    {
                        "name": "optimize_shipping",
                        "agent": "supply-chain-agent",
                        "action": "optimize_shipping_options",
                        "parameters": {}
                    },
                    {
                        "name": "process_payment",
                        "agent": "payment-processor-agent",
                        "action": "process_secure_payment",
                        "parameters": {}
                    },
                    {
                        "name": "send_confirmation",
                        "agent": "communication-agent",
                        "action": "send_order_confirmation",
                        "parameters": {}
                    }
                ]
            },
            "inventory_optimization": {
                "name": "Inventory Optimization Workflow",
                "description": "AI-driven inventory management and forecasting",
                "steps": [
                    {
                        "name": "analyze_demand",
                        "agent": "analytics-agent",
                        "action": "analyze_demand_patterns",
                        "parameters": {}
                    },
                    {
                        "name": "forecast_inventory",
                        "agent": "supply-chain-agent",
                        "action": "forecast_inventory_needs",
                        "parameters": {}
                    },
                    {
                        "name": "optimize_pricing",
                        "agent": "pricing-optimizer-agent",
                        "action": "optimize_inventory_pricing",
                        "parameters": {}
                    },
                    {
                        "name": "plan_procurement",
                        "agent": "supply-chain-agent",
                        "action": "plan_procurement_strategy",
                        "parameters": {}
                    }
                ]
            },
            "customer_support": {
                "name": "Intelligent Customer Support Workflow",
                "description": "AI-powered customer support with escalation management",
                "steps": [
                    {
                        "name": "analyze_inquiry",
                        "agent": "support-agent",
                        "action": "analyze_customer_inquiry",
                        "parameters": {}
                    },
                    {
                        "name": "search_knowledge_base",
                        "agent": "knowledge-agent",
                        "action": "search_solutions",
                        "parameters": {}
                    },
                    {
                        "name": "generate_response",
                        "agent": "communication-agent",
                        "action": "generate_personalized_response",
                        "parameters": {}
                    },
                    {
                        "name": "determine_escalation",
                        "agent": "support-agent",
                        "action": "evaluate_escalation_need",
                        "parameters": {}
                    }
                ]
            }
        }
    
    def setup_message_handlers(self):
        """Setup A2A message handlers"""
        self.a2a_engine.register_handler("execute_workflow", self.handle_workflow_execution)
        self.a2a_engine.register_handler("get_workflow_status", self.handle_workflow_status)
        self.a2a_engine.register_handler("list_workflows", self.handle_list_workflows)
        self.a2a_engine.register_handler("cancel_workflow", self.handle_cancel_workflow)
    
    async def start(self):
        """Start the orchestrator"""
        logger.info("Starting Multi-Agent Orchestrator")
        await self.a2a_engine.start()
        await self.workflow_engine.start()
        logger.info("Multi-Agent Orchestrator started successfully")
    
    async def stop(self):
        """Stop the orchestrator"""
        logger.info("Stopping Multi-Agent Orchestrator")
        await self.workflow_engine.stop()
        await self.a2a_engine.stop()
        logger.info("Multi-Agent Orchestrator stopped")
    
    async def execute_workflow(
        self, 
        workflow_type: str, 
        user_id: str, 
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a predefined workflow"""
        
        if workflow_type not in self.workflow_templates:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        # Get workflow template
        template = self.workflow_templates[workflow_type].copy()
        
        # Enrich workflow with user context
        workflow_definition = await self.prepare_workflow(template, user_id, parameters, context)
        
        # Execute workflow
        result = await self.workflow_engine.execute_workflow(workflow_definition)
        
        # Store in active workflows
        self.active_workflows[result["id"]] = result
        
        return result
    
    async def prepare_workflow(
        self, 
        template: Dict[str, Any], 
        user_id: str, 
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare workflow with user-specific context and parameters"""
        
        workflow_definition = template.copy()
        
        # Add user context to all steps
        for step in workflow_definition["steps"]:
            step["parameters"].update({
                "user_id": user_id,
                "user_context": context or {},
                "workflow_parameters": parameters
            })
        
        # Add metadata
        workflow_definition["metadata"] = {
            "user_id": user_id,
            "created_at": time.time(),
            "orchestrator": self.agent_id,
            "parameters": parameters,
            "context": context
        }
        
        return workflow_definition
    
    async def handle_workflow_execution(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow execution request via A2A"""
        try:
            workflow_type = payload["workflow_type"]
            user_id = payload["user_id"]
            parameters = payload.get("parameters", {})
            context = payload.get("context")
            
            result = await self.execute_workflow(workflow_type, user_id, parameters, context)
            
            return {
                "success": True,
                "workflow_id": result["id"],
                "status": result["status"],
                "steps_completed": len(result["steps"]),
                "total_steps": len(result["definition"]["steps"])
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_workflow_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow status request"""
        workflow_id = payload.get("workflow_id")
        
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": workflow["status"],
                "steps": workflow["steps"],
                "results": workflow["results"],
                "duration": workflow.get("duration", time.time() - workflow["start_time"])
            }
        else:
            return {"success": False, "error": "Workflow not found"}
    
    async def handle_list_workflows(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list workflows request"""
        user_id = payload.get("user_id")
        
        workflows = []
        for workflow_id, workflow in self.active_workflows.items():
            if not user_id or workflow["definition"]["metadata"]["user_id"] == user_id:
                workflows.append({
                    "id": workflow_id,
                    "type": workflow["definition"].get("name", "Unknown"),
                    "status": workflow["status"],
                    "created_at": workflow["definition"]["metadata"]["created_at"],
                    "steps_completed": len(workflow["steps"]),
                    "total_steps": len(workflow["definition"]["steps"])
                })
        
        return {"success": True, "workflows": workflows}
    
    async def handle_cancel_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow cancellation request"""
        workflow_id = payload.get("workflow_id")
        
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["status"] = "cancelled"
            return {"success": True, "message": "Workflow cancelled"}
        else:
            return {"success": False, "error": "Workflow not found"}
    
    # AgentInterface implementation
    async def handle_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Handle incoming A2A message"""
        return await self.a2a_engine.handle_incoming_message(message)
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return orchestrator capabilities"""
        return [
            AgentCapability.SHOPPING_ASSISTANCE,
            AgentCapability.CUSTOMER_JOURNEY,
            AgentCapability.PRICING_OPTIMIZATION,
            AgentCapability.SUPPLY_CHAIN,
            AgentCapability.SECURITY_ANALYSIS
        ]
    
    def get_agent_id(self) -> str:
        """Return agent ID"""
        return self.agent_id

# FastAPI Application
app = FastAPI(title="Multi-Agent Orchestrator", version="1.0.0")

# Global orchestrator instance
orchestrator = MultiAgentOrchestrator()

@app.on_event("startup")
async def startup():
    """Start orchestrator on application startup"""
    await orchestrator.start()

@app.on_event("shutdown")
async def shutdown():
    """Stop orchestrator on application shutdown"""
    await orchestrator.stop()

@app.post("/workflows/execute", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest):
    """Execute a workflow"""
    try:
        result = await orchestrator.execute_workflow(
            request.workflow_type,
            request.user_id,
            request.parameters,
            request.context
        )
        
        return WorkflowResponse(
            workflow_id=result["id"],
            status=result["status"],
            results=result["results"],
            duration=result.get("duration", 0),
            steps_completed=len(result["steps"]),
            total_steps=len(result["definition"]["steps"])
        )
        
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get workflow status"""
    if workflow_id in orchestrator.active_workflows:
        workflow = orchestrator.active_workflows[workflow_id]
        return {
            "workflow_id": workflow_id,
            "status": workflow["status"],
            "steps": workflow["steps"],
            "results": workflow["results"],
            "duration": workflow.get("duration", time.time() - workflow["start_time"])
        }
    else:
        raise HTTPException(status_code=404, detail="Workflow not found")

@app.get("/workflows")
async def list_workflows(user_id: Optional[str] = None):
    """List workflows"""
    workflows = []
    for workflow_id, workflow in orchestrator.active_workflows.items():
        if not user_id or workflow["definition"]["metadata"]["user_id"] == user_id:
            workflows.append({
                "id": workflow_id,
                "type": workflow["definition"].get("name", "Unknown"),
                "status": workflow["status"],
                "created_at": workflow["definition"]["metadata"]["created_at"],
                "steps_completed": len(workflow["steps"]),
                "total_steps": len(workflow["definition"]["steps"])
            })
    
    return {"workflows": workflows}

@app.get("/workflow-templates")
async def list_workflow_templates():
    """List available workflow templates"""
    templates = []
    for template_id, template in orchestrator.workflow_templates.items():
        templates.append({
            "id": template_id,
            "name": template["name"],
            "description": template["description"],
            "steps": len(template["steps"])
        })
    
    return {"templates": templates}

@app.delete("/workflows/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """Cancel a workflow"""
    if workflow_id in orchestrator.active_workflows:
        orchestrator.active_workflows[workflow_id]["status"] = "cancelled"
        return {"message": "Workflow cancelled"}
    else:
        raise HTTPException(status_code=404, detail="Workflow not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "multi-agent-orchestrator",
        "active_workflows": len(orchestrator.active_workflows),
        "workflow_templates": len(orchestrator.workflow_templates)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)