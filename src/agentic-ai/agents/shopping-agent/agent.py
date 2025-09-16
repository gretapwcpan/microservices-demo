#!/usr/bin/env python3
"""
Simplified Gemini-Powered Shopping Agent for Online Boutique
Clean, minimal implementation without unnecessary complexity
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional

import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Shopping Agent", version="2.0.0")

# Configure Gemini - REQUIRED
api_key = os.getenv('GOOGLE_AI_API_KEY')

if not api_key:
    logger.error("GOOGLE_AI_API_KEY environment variable is required")
    raise ValueError("GOOGLE_AI_API_KEY environment variable must be set")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini AI configured successfully")
except Exception as e:
    logger.error(f"Failed to configure Gemini: {e}")
    raise

# MCP Server URL
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://mcp-server:8080')

# Request/Response models
class ChatRequest(BaseModel):
    user_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    success: bool
    products: Optional[list] = []
    actions_performed: Optional[list] = []

# System prompt for Gemini
SYSTEM_PROMPT = """You are a helpful shopping assistant for Online Boutique.
When a user asks about products or shopping, analyze their request and respond with a JSON object:
{
    "intent": "search|browse|add_to_cart|get_cart|help",
    "parameters": {
        "query": "search term if searching",
        "product_id": "product ID if adding to cart",
        "quantity": 1
    },
    "friendly_response": "A friendly message to the user"
}

Be concise, helpful, and friendly. Focus on understanding what the user wants to do."""

def call_mcp_server(tool: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Call MCP Server to interact with microservices"""
    try:
        response = requests.post(
            f"{MCP_SERVER_URL}/mcp/call",
            json={"tool": tool, "parameters": parameters},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"MCP Server returned {response.status_code}")
            return {"success": False, "error": f"MCP Server error: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error calling MCP Server: {e}")
        return {"success": False, "error": str(e)}

def parse_gemini_response(response_text: str) -> Dict[str, Any]:
    """Parse Gemini's response to extract intent and parameters"""
    try:
        # Try to extract JSON from the response
        if "{" in response_text and "}" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            return json.loads(json_str)
        else:
            # Fallback if no JSON found
            return {
                "intent": "help",
                "parameters": {},
                "friendly_response": response_text
            }
    except Exception as e:
        logger.warning(f"Could not parse Gemini response: {e}")
        return {
            "intent": "help",
            "parameters": {},
            "friendly_response": response_text
        }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - powered by Gemini AI"""
    try:
        # Use Gemini to understand the user's intent
        prompt = f"{SYSTEM_PROMPT}\n\nUser ({request.user_id}): {request.message}"
        
        try:
            gemini_response = model.generate_content(prompt)
            
            # Check if response is valid
            if not gemini_response or not gemini_response.text:
                logger.warning("Empty response from Gemini")
                return ChatResponse(
                    response="I'm having trouble understanding. Could you please rephrase your request?",
                    success=True,
                    products=[],
                    actions_performed=[]
                )
                
        except Exception as gemini_error:
            logger.error(f"Gemini API error: {gemini_error}")
            return ChatResponse(
                response="I'm experiencing technical difficulties. Please try again in a moment.",
                success=False,
                products=[],
                actions_performed=[]
            )
        
        # Parse Gemini's response
        parsed = parse_gemini_response(gemini_response.text)
        intent = parsed.get("intent", "help")
        parameters = parsed.get("parameters", {})
        friendly_response = parsed.get("friendly_response", "How can I help you shop today?")
        
        actions_performed = []
        products = []
        
        # Execute actions based on intent
        if intent == "search" and "query" in parameters:
            # Search for products
            result = call_mcp_server("search_products", {"query": parameters["query"]})
            if result.get("success"):
                product_list = result.get("data", {}).get("products", [])
                products = [p.get("id") for p in product_list[:5]]  # Top 5 products
                actions_performed.append(f"Searched for: {parameters['query']}")
                if products:
                    friendly_response += f"\n\nI found {len(product_list)} products. Here are the top results."
                else:
                    friendly_response = f"I couldn't find any products matching '{parameters['query']}'."
        
        elif intent == "add_to_cart" and "product_id" in parameters:
            # Add item to cart
            cart_params = {
                "user_id": request.user_id,
                "product_id": parameters["product_id"],
                "quantity": parameters.get("quantity", 1)
            }
            result = call_mcp_server("add_to_cart", cart_params)
            if result.get("success"):
                actions_performed.append(f"Added to cart: {parameters['product_id']}")
                friendly_response += "\n\nI've added that item to your cart!"
            else:
                friendly_response = "I had trouble adding that item to your cart. Please try again."
        
        elif intent == "get_cart":
            # Get cart contents
            result = call_mcp_server("get_cart", {"user_id": request.user_id})
            if result.get("success"):
                cart_items = result.get("data", {}).get("items", [])
                actions_performed.append("Retrieved cart contents")
                if cart_items:
                    friendly_response += f"\n\nYou have {len(cart_items)} items in your cart."
                else:
                    friendly_response = "Your cart is currently empty."
        
        elif intent == "browse":
            # Browse all products
            result = call_mcp_server("search_products", {"query": ""})
            if result.get("success"):
                product_list = result.get("data", {}).get("products", [])
                products = [p.get("id") for p in product_list[:8]]  # Top 8 products
                actions_performed.append("Browsed catalog")
                friendly_response += f"\n\nHere are some of our featured products!"
        
        return ChatResponse(
            response=friendly_response,
            success=True,
            products=products,
            actions_performed=actions_performed
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return ChatResponse(
            response=f"I encountered an error: {str(e)}",
            success=False,
            products=[],
            actions_performed=[]
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {
        "status": "healthy",
        "service": "shopping-agent",
        "version": "2.0.0",
        "gemini_configured": model is not None,
        "mcp_server_url": MCP_SERVER_URL
    }

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Shopping Agent",
        "description": "Simplified Gemini-powered shopping assistant",
        "endpoints": {
            "/chat": "POST - Chat with the shopping agent",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
