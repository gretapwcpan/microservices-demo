#!/usr/bin/env python3
"""
Agent2Agent (A2A) Protocol Implementation
Enables secure and efficient communication between AI agents
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
import aiohttp
import websockets
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """A2A message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_STEP = "workflow_step"
    WORKFLOW_END = "workflow_end"

class AgentCapability(Enum):
    """Agent capability types"""
    SHOPPING_ASSISTANCE = "shopping_assistance"
    PRICING_OPTIMIZATION = "pricing_optimization"
    CUSTOMER_JOURNEY = "customer_journey"
    SUPPLY_CHAIN = "supply_chain"
    SECURITY_ANALYSIS = "security_analysis"
    RECOMMENDATION = "recommendation"
    SEARCH = "search"
    PAYMENT_PROCESSING = "payment_processing"

@dataclass
class A2AMessage:
    """Standard A2A protocol message"""
    id: str
    type: MessageType
    source_agent: str
    target_agent: Optional[str]
    timestamp: float
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    priority: int = 5  # 1=highest, 10=lowest
    ttl: Optional[float] = None  # Time to live in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "workflow_id": self.workflow_id,
            "priority": self.priority,
            "ttl": self.ttl
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            source_agent=data["source_agent"],
            target_agent=data.get("target_agent"),
            timestamp=data["timestamp"],
            payload=data["payload"],
            correlation_id=data.get("correlation_id"),
            workflow_id=data.get("workflow_id"),
            priority=data.get("priority", 5),
            ttl=data.get("ttl")
        )

class AgentInterface(ABC):
    """Abstract interface for A2A-enabled agents"""
    
    @abstractmethod
    async def handle_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Handle incoming A2A message"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities"""
        pass
    
    @abstractmethod
    def get_agent_id(self) -> str:
        """Return unique agent identifier"""
        pass

class A2AProtocolEngine:
    """Core A2A protocol engine for message routing and management"""
    
    def __init__(self, agent_id: str, broker_url: str = "ws://a2a-broker:8082"):
        self.agent_id = agent_id
        self.broker_url = broker_url
        self.connected_agents: Dict[str, str] = {}  # agent_id -> websocket_url
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.websocket = None
        self.running = False
        
    async def start(self):
        """Start A2A protocol engine"""
        self.running = True
        try:
            self.websocket = await websockets.connect(self.broker_url)
            
            # Register with broker
            await self.register_agent()
            
            # Start message processing loop
            await asyncio.gather(
                self.message_processor(),
                self.heartbeat_sender()
            )
        except Exception as e:
            logger.error(f"Error starting A2A engine: {e}")
            raise
    
    async def stop(self):
        """Stop A2A protocol engine"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
    
    async def register_agent(self):
        """Register agent with A2A broker"""
        registration_message = A2AMessage(
            id=str(uuid.uuid4()),
            type=MessageType.NOTIFICATION,
            source_agent=self.agent_id,
            target_agent="broker",
            timestamp=time.time(),
            payload={
                "action": "register",
                "agent_id": self.agent_id,
                "capabilities": [cap.value for cap in self.get_capabilities()],
                "endpoints": {
                    "websocket": self.broker_url,
                    "http": f"http://{self.agent_id}:8080"
                }
            }
        )
        
        await self.websocket.send(json.dumps(registration_message.to_dict()))
        logger.info(f"Agent {self.agent_id} registered with A2A broker")
    
    async def send_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Send A2A message to another agent"""
        if message.type == MessageType.REQUEST:
            # For requests, wait for response
            future = asyncio.Future()
            self.pending_requests[message.id] = future
            
            await self.websocket.send(json.dumps(message.to_dict()))
            
            try:
                # Wait for response with timeout
                response = await asyncio.wait_for(future, timeout=30.0)
                return response
            except asyncio.TimeoutError:
                logger.error(f"Request {message.id} timed out")
                del self.pending_requests[message.id]
                return None
        else:
            # For notifications and other message types
            await self.websocket.send(json.dumps(message.to_dict()))
            return None
    
    async def message_processor(self):
        """Process incoming messages"""
        while self.running:
            try:
                raw_message = await self.websocket.recv()
                message_data = json.loads(raw_message)
                message = A2AMessage.from_dict(message_data)
                
                # Handle response to pending request
                if message.type == MessageType.RESPONSE and message.correlation_id:
                    if message.correlation_id in self.pending_requests:
                        future = self.pending_requests[message.correlation_id]
                        future.set_result(message)
                        del self.pending_requests[message.correlation_id]
                        continue
                
                # Handle incoming request or notification
                if message.target_agent == self.agent_id or message.target_agent is None:
                    await self.handle_incoming_message(message)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("A2A connection closed")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def handle_incoming_message(self, message: A2AMessage):
        """Handle incoming message from another agent"""
        try:
            # Route to appropriate handler
            if message.payload.get("action") in self.message_handlers:
                handler = self.message_handlers[message.payload["action"]]
                response_payload = await handler(message.payload)
                
                # Send response if it was a request
                if message.type == MessageType.REQUEST:
                    response = A2AMessage(
                        id=str(uuid.uuid4()),
                        type=MessageType.RESPONSE,
                        source_agent=self.agent_id,
                        target_agent=message.source_agent,
                        timestamp=time.time(),
                        payload=response_payload,
                        correlation_id=message.id
                    )
                    
                    await self.websocket.send(json.dumps(response.to_dict()))
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
            # Send error response
            if message.type == MessageType.REQUEST:
                error_response = A2AMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.ERROR,
                    source_agent=self.agent_id,
                    target_agent=message.source_agent,
                    timestamp=time.time(),
                    payload={"error": str(e)},
                    correlation_id=message.id
                )
                
                await self.websocket.send(json.dumps(error_response.to_dict()))
    
    async def heartbeat_sender(self):
        """Send periodic heartbeat messages"""
        while self.running:
            try:
                heartbeat = A2AMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.HEARTBEAT,
                    source_agent=self.agent_id,
                    target_agent="broker",
                    timestamp=time.time(),
                    payload={"status": "healthy"}
                )
                
                await self.websocket.send(json.dumps(heartbeat.to_dict()))
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                break
    
    def register_handler(self, action: str, handler: Callable):
        """Register message handler for specific action"""
        self.message_handlers[action] = handler
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Override in subclasses"""
        return []

class A2AWorkflowEngine:
    """Workflow orchestration engine using A2A protocol"""
    
    def __init__(self, orchestrator_id: str):
        self.orchestrator_id = orchestrator_id
        self.a2a_engine = A2AProtocolEngine(orchestrator_id)
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
    
    async def start(self):
        """Start workflow engine"""
        await self.a2a_engine.start()
    
    async def stop(self):
        """Stop workflow engine"""
        await self.a2a_engine.stop()
    
    async def execute_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a multi-agent workflow"""
        workflow_id = str(uuid.uuid4())
        
        try:
            # Initialize workflow
            workflow_state = {
                "id": workflow_id,
                "definition": workflow_definition,
                "status": "running",
                "steps": [],
                "results": {},
                "start_time": time.time()
            }
            
            self.active_workflows[workflow_id] = workflow_state
            
            # Execute workflow steps
            for step in workflow_definition["steps"]:
                step_result = await self.execute_workflow_step(workflow_id, step)
                workflow_state["steps"].append(step_result)
                workflow_state["results"][step["name"]] = step_result
                
                # Check if step failed
                if not step_result.get("success", False):
                    workflow_state["status"] = "failed"
                    break
            
            # Mark as completed if all steps succeeded
            if workflow_state["status"] == "running":
                workflow_state["status"] = "completed"
            
            workflow_state["end_time"] = time.time()
            workflow_state["duration"] = workflow_state["end_time"] - workflow_state["start_time"]
            
            return workflow_state
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = "error"
                self.active_workflows[workflow_id]["error"] = str(e)
            raise
    
    async def execute_workflow_step(self, workflow_id: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        try:
            step_start = time.time()
            
            # Create A2A message for the step
            message = A2AMessage(
                id=str(uuid.uuid4()),
                type=MessageType.REQUEST,
                source_agent=self.orchestrator_id,
                target_agent=step["agent"],
                timestamp=time.time(),
                payload={
                    "action": step["action"],
                    "parameters": step.get("parameters", {}),
                    "workflow_id": workflow_id,
                    "step_name": step["name"]
                },
                workflow_id=workflow_id
            )
            
            # Send message and wait for response
            response = await self.a2a_engine.send_message(message)
            
            step_result = {
                "name": step["name"],
                "agent": step["agent"],
                "action": step["action"],
                "start_time": step_start,
                "end_time": time.time(),
                "duration": time.time() - step_start,
                "success": response is not None and response.type != MessageType.ERROR,
                "response": response.payload if response else None,
                "error": response.payload.get("error") if response and response.type == MessageType.ERROR else None
            }
            
            return step_result
            
        except Exception as e:
            logger.error(f"Workflow step {step['name']} failed: {e}")
            return {
                "name": step["name"],
                "agent": step["agent"],
                "action": step["action"],
                "start_time": step_start,
                "end_time": time.time(),
                "duration": time.time() - step_start,
                "success": False,
                "error": str(e)
            }

class A2ABroker:
    """Central message broker for A2A protocol"""
    
    def __init__(self, port: int = 8082):
        self.port = port
        self.connected_agents: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
    async def start_server(self):
        """Start A2A broker server"""
        logger.info(f"Starting A2A broker on port {self.port}")
        
        async def handle_client(websocket, path):
            try:
                async for message in websocket:
                    await self.handle_message(websocket, message)
            except websockets.exceptions.ConnectionClosed:
                await self.handle_disconnect(websocket)
        
        start_server = websockets.serve(handle_client, "0.0.0.0", self.port)
        await start_server
        
        # Start message processor
        asyncio.create_task(self.process_message_queue())
    
    async def handle_message(self, websocket, raw_message: str):
        """Handle incoming message from agent"""
        try:
            message_data = json.loads(raw_message)
            message = A2AMessage.from_dict(message_data)
            
            # Handle registration
            if (message.payload.get("action") == "register" and 
                message.target_agent == "broker"):
                await self.register_agent(websocket, message)
                return
            
            # Handle heartbeat
            if message.type == MessageType.HEARTBEAT:
                logger.debug(f"Heartbeat from {message.source_agent}")
                return
            
            # Route message to target agent
            await self.route_message(message)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def register_agent(self, websocket, message: A2AMessage):
        """Register a new agent"""
        agent_id = message.payload["agent_id"]
        capabilities = message.payload.get("capabilities", [])
        
        self.connected_agents[agent_id] = websocket
        self.agent_capabilities[agent_id] = capabilities
        
        logger.info(f"Registered agent {agent_id} with capabilities: {capabilities}")
    
    async def route_message(self, message: A2AMessage):
        """Route message to target agent"""
        target_agent = message.target_agent
        
        if target_agent and target_agent in self.connected_agents:
            target_websocket = self.connected_agents[target_agent]
            try:
                await target_websocket.send(json.dumps(message.to_dict()))
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Target agent {target_agent} disconnected")
                del self.connected_agents[target_agent]
        else:
            # Broadcast to all agents if no specific target
            for agent_id, websocket in self.connected_agents.items():
                if agent_id != message.source_agent:
                    try:
                        await websocket.send(json.dumps(message.to_dict()))
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning(f"Agent {agent_id} disconnected")
    
    async def handle_disconnect(self, websocket):
        """Handle agent disconnection"""
        # Find and remove disconnected agent
        for agent_id, ws in list(self.connected_agents.items()):
            if ws == websocket:
                del self.connected_agents[agent_id]
                if agent_id in self.agent_capabilities:
                    del self.agent_capabilities[agent_id]
                logger.info(f"Agent {agent_id} disconnected")
                break
    
    async def process_message_queue(self):
        """Process queued messages"""
        while True:
            try:
                message = await self.message_queue.get()
                await self.route_message(message)
                self.message_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")

# FastAPI server for A2A broker management
from fastapi import FastAPI

def create_broker_app() -> FastAPI:
    """Create FastAPI app for A2A broker management"""
    app = FastAPI(title="A2A Protocol Broker", version="1.0.0")
    broker = A2ABroker()
    
    @app.on_event("startup")
    async def startup():
        await broker.start_server()
    
    @app.get("/agents")
    async def list_agents():
        """List connected agents"""
        return {
            "agents": list(broker.connected_agents.keys()),
            "capabilities": broker.agent_capabilities
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "connected_agents": len(broker.connected_agents),
            "service": "a2a-broker"
        }
    
    return app

if __name__ == "__main__":
    import uvicorn
    app = create_broker_app()
    uvicorn.run(app, host="0.0.0.0", port=8083)