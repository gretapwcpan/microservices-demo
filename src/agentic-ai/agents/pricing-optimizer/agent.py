#!/usr/bin/env python3
"""
Pricing Optimizer Agent
AI-powered dynamic pricing and revenue optimization
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
import requests
import numpy as np
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from a2a_protocol.protocol import (
    A2AProtocolEngine, A2AMessage, MessageType, 
    AgentCapability, AgentInterface
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PricingOptimizerAgent(AgentInterface):
    """AI-powered pricing optimization agent using Gemini"""
    
    def __init__(self, mcp_server_url: str = "http://mcp-server:8080"):
        self.agent_id = "pricing-optimizer-agent"
        self.mcp_server_url = mcp_server_url
        self.a2a_engine = A2AProtocolEngine(self.agent_id)
        self.setup_gemini()
        self.setup_message_handlers()
        
        # Pricing models and strategies
        self.pricing_strategies = {
            "competitive": self.competitive_pricing,
            "demand_based": self.demand_based_pricing,
            "value_based": self.value_based_pricing,
            "dynamic": self.dynamic_pricing,
            "promotional": self.promotional_pricing
        }
        
        # Market data cache
        self.market_data_cache = {}
        self.last_market_update = 0
    
    def setup_gemini(self):
        """Initialize Gemini models for pricing analysis"""
        api_key = os.getenv('GOOGLE_AI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
        
        self.gemini_pro = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.1  # Low temperature for consistent pricing decisions
        )
        
        self.gemini_flash = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.2
        )
    
    def setup_message_handlers(self):
        """Setup A2A message handlers"""
        self.a2a_engine.register_handler("optimize_product_pricing", self.handle_product_pricing)
        self.a2a_engine.register_handler("analyze_price_elasticity", self.handle_price_elasticity)
        self.a2a_engine.register_handler("optimize_inventory_pricing", self.handle_inventory_pricing)
        self.a2a_engine.register_handler("generate_pricing_strategy", self.handle_pricing_strategy)
        self.a2a_engine.register_handler("analyze_competitor_pricing", self.handle_competitor_analysis)
    
    async def start(self):
        """Start the pricing optimizer agent"""
        logger.info("Starting Pricing Optimizer Agent")
        await self.a2a_engine.start()
    
    async def stop(self):
        """Stop the pricing optimizer agent"""
        logger.info("Stopping Pricing Optimizer Agent")
        await self.a2a_engine.stop()
    
    async def handle_product_pricing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle product pricing optimization request"""
        try:
            user_id = payload.get("user_id")
            products = payload.get("products", [])
            strategy = payload.get("strategy", "dynamic")
            constraints = payload.get("constraints", {})
            
            # Get current product data
            product_data = await self.get_product_data(products)
            
            # Analyze market conditions
            market_analysis = await self.analyze_market_conditions(products)
            
            # Apply pricing strategy
            pricing_results = await self.apply_pricing_strategy(
                strategy, product_data, market_analysis, constraints
            )
            
            return {
                "success": True,
                "pricing_results": pricing_results,
                "strategy_used": strategy,
                "market_analysis": market_analysis,
                "optimization_score": pricing_results.get("optimization_score", 0)
            }
            
        except Exception as e:
            logger.error(f"Error in product pricing: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_price_elasticity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle price elasticity analysis request"""
        try:
            products = payload.get("products", [])
            historical_data = payload.get("historical_data", {})
            
            elasticity_analysis = await self.analyze_price_elasticity(products, historical_data)
            
            return {
                "success": True,
                "elasticity_analysis": elasticity_analysis,
                "recommendations": elasticity_analysis.get("recommendations", [])
            }
            
        except Exception as e:
            logger.error(f"Error in price elasticity analysis: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_inventory_pricing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inventory-based pricing optimization"""
        try:
            inventory_data = payload.get("inventory_data", {})
            demand_forecast = payload.get("demand_forecast", {})
            objectives = payload.get("objectives", ["maximize_revenue"])
            
            inventory_pricing = await self.optimize_inventory_pricing(
                inventory_data, demand_forecast, objectives
            )
            
            return {
                "success": True,
                "inventory_pricing": inventory_pricing,
                "expected_revenue_impact": inventory_pricing.get("revenue_impact", 0)
            }
            
        except Exception as e:
            logger.error(f"Error in inventory pricing: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_pricing_strategy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pricing strategy generation request"""
        try:
            business_objectives = payload.get("business_objectives", [])
            market_position = payload.get("market_position", "mid_market")
            competitive_landscape = payload.get("competitive_landscape", {})
            
            strategy = await self.generate_pricing_strategy(
                business_objectives, market_position, competitive_landscape
            )
            
            return {
                "success": True,
                "pricing_strategy": strategy,
                "implementation_plan": strategy.get("implementation_plan", [])
            }
            
        except Exception as e:
            logger.error(f"Error generating pricing strategy: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_competitor_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle competitor pricing analysis request"""
        try:
            products = payload.get("products", [])
            competitors = payload.get("competitors", [])
            
            competitor_analysis = await self.analyze_competitor_pricing(products, competitors)
            
            return {
                "success": True,
                "competitor_analysis": competitor_analysis,
                "pricing_opportunities": competitor_analysis.get("opportunities", [])
            }
            
        except Exception as e:
            logger.error(f"Error in competitor analysis: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_product_data(self, product_ids: List[str]) -> Dict[str, Any]:
        """Get current product data via MCP"""
        product_data = {}
        
        for product_id in product_ids:
            try:
                response = requests.post(
                    f"{self.mcp_server_url}/mcp/call",
                    json={
                        "tool": "get_product",
                        "parameters": {"product_id": product_id}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        product_data[product_id] = result["data"]
                        
            except Exception as e:
                logger.error(f"Error getting product {product_id}: {e}")
        
        return product_data
    
    async def analyze_market_conditions(self, products: List[str]) -> Dict[str, Any]:
        """Analyze current market conditions using Gemini"""
        
        # Get product categories for market analysis
        categories = set()
        for product_id in products:
            try:
                response = requests.post(
                    f"{self.mcp_server_url}/mcp/call",
                    json={
                        "tool": "get_product",
                        "parameters": {"product_id": product_id}
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        product_categories = result["data"].get("categories", [])
                        categories.update(product_categories)
            except Exception as e:
                logger.warning(f"Could not get categories for product {product_id}: {e}")
        
        market_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are an expert market analyst specializing in e-commerce pricing strategy.
            
            Analyze the current market conditions for the given product categories and provide:
            
            1. Market trends and seasonality factors
            2. Demand patterns and elasticity estimates
            3. Competitive intensity assessment
            4. Price sensitivity indicators
            5. Recommended pricing adjustments
            
            Return your analysis as a structured JSON response with:
            {{
                "market_trends": {{...}},
                "demand_patterns": {{...}},
                "competitive_intensity": "low|medium|high",
                "price_sensitivity": "low|medium|high",
                "seasonal_factors": {{...}},
                "recommended_adjustments": {{...}},
                "confidence_score": 0.0-1.0
            }}
            """),
            ("human", f"""
            Analyze market conditions for these product categories: {list(categories)}
            
            Consider current date: {time.strftime('%Y-%m-%d')}
            Products to analyze: {products}
            """)
        ])
        
        try:
            response = await self.gemini_pro.ainvoke(market_prompt.format_messages())
            
            # Try to parse JSON from response
            response_text = response.content
            if "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                return {
                    "analysis": response_text,
                    "confidence_score": 0.7,
                    "competitive_intensity": "medium",
                    "price_sensitivity": "medium"
                }
                
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return {
                "error": str(e),
                "confidence_score": 0.3,
                "competitive_intensity": "medium",
                "price_sensitivity": "medium"
            }
    
    async def apply_pricing_strategy(
        self, 
        strategy: str, 
        product_data: Dict[str, Any], 
        market_analysis: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply selected pricing strategy"""
        
        if strategy in self.pricing_strategies:
            return await self.pricing_strategies[strategy](
                product_data, market_analysis, constraints
            )
        else:
            return await self.dynamic_pricing(product_data, market_analysis, constraints)
    
    async def competitive_pricing(
        self, 
        product_data: Dict[str, Any], 
        market_analysis: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Competitive pricing strategy"""
        
        pricing_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a competitive pricing specialist. Analyze the products and market data to recommend 
            competitive pricing that maintains market position while optimizing margins.
            
            Consider:
            - Current product prices and costs
            - Market competitive intensity
            - Brand positioning requirements
            - Margin constraints
            
            Return JSON with recommended prices and reasoning:
            {{
                "product_recommendations": {{
                    "product_id": {{
                        "current_price": float,
                        "recommended_price": float,
                        "adjustment_percentage": float,
                        "reasoning": "string",
                        "competitive_position": "premium|market|value"
                    }}
                }},
                "strategy_summary": "string",
                "expected_impact": "string",
                "optimization_score": float
            }}
            """),
            ("human", f"""
            Product Data: {json.dumps(product_data, indent=2)}
            Market Analysis: {json.dumps(market_analysis, indent=2)}
            Constraints: {json.dumps(constraints, indent=2)}
            """)
        ])
        
        try:
            response = await self.gemini_pro.ainvoke(pricing_prompt.format_messages())
            response_text = response.content
            
            if "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error in competitive pricing: {e}")
        
        # Fallback: simple competitive adjustment
        recommendations = {}
        for product_id, product in product_data.items():
            current_price = product.get("price_usd", {})
            price_value = current_price.get("units", 0) + current_price.get("nanos", 0) / 1e9
            
            # Simple competitive adjustment (5% below market if high competition)
            adjustment = -0.05 if market_analysis.get("competitive_intensity") == "high" else 0.02
            new_price = price_value * (1 + adjustment)
            
            recommendations[product_id] = {
                "current_price": price_value,
                "recommended_price": new_price,
                "adjustment_percentage": adjustment * 100,
                "reasoning": f"Competitive adjustment for {market_analysis.get('competitive_intensity', 'medium')} competition"
            }
        
        return {
            "product_recommendations": recommendations,
            "strategy_summary": "Competitive pricing with market positioning",
            "optimization_score": 0.75
        }
    
    async def demand_based_pricing(
        self, 
        product_data: Dict[str, Any], 
        market_analysis: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Demand-based pricing strategy"""
        # Implementation for demand-based pricing
        return await self.competitive_pricing(product_data, market_analysis, constraints)
    
    async def value_based_pricing(
        self, 
        product_data: Dict[str, Any], 
        market_analysis: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Value-based pricing strategy"""
        # Implementation for value-based pricing
        return await self.competitive_pricing(product_data, market_analysis, constraints)
    
    async def dynamic_pricing(
        self, 
        product_data: Dict[str, Any], 
        market_analysis: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dynamic pricing strategy with real-time adjustments"""
        return await self.competitive_pricing(product_data, market_analysis, constraints)
    
    async def promotional_pricing(
        self, 
        product_data: Dict[str, Any], 
        market_analysis: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Promotional pricing strategy"""
        return await self.competitive_pricing(product_data, market_analysis, constraints)
    
    async def analyze_price_elasticity(
        self, 
        products: List[str], 
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze price elasticity using historical data"""
        
        elasticity_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a pricing economist specializing in price elasticity analysis.
            
            Analyze the historical sales and pricing data to determine price elasticity
            and provide actionable recommendations.
            
            Return JSON analysis:
            {{
                "elasticity_coefficients": {{
                    "product_id": float  // negative values indicate normal goods
                }},
                "price_sensitivity_categories": {{
                    "elastic": [product_ids],
                    "inelastic": [product_ids], 
                    "unit_elastic": [product_ids]
                }},
                "recommendations": [
                    {{
                        "product_id": "string",
                        "recommendation": "increase|decrease|maintain",
                        "suggested_change": float,
                        "expected_demand_impact": "string"
                    }}
                ],
                "confidence_level": float
            }}
            """),
            ("human", f"""
            Products: {products}
            Historical Data: {json.dumps(historical_data, indent=2)}
            """)
        ])
        
        try:
            response = await self.gemini_pro.ainvoke(elasticity_prompt.format_messages())
            response_text = response.content
            
            if "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
                
        except Exception as e:
            logger.error(f"Error in elasticity analysis: {e}")
        
        # Fallback analysis
        return {
            "elasticity_coefficients": {pid: -0.8 for pid in products},
            "price_sensitivity_categories": {
                "elastic": products[:len(products)//2],
                "inelastic": products[len(products)//2:],
                "unit_elastic": []
            },
            "recommendations": [
                {
                    "product_id": pid,
                    "recommendation": "maintain",
                    "suggested_change": 0,
                    "expected_demand_impact": "No significant change expected"
                } for pid in products
            ],
            "confidence_level": 0.6
        }
    
    async def optimize_inventory_pricing(
        self, 
        inventory_data: Dict[str, Any], 
        demand_forecast: Dict[str, Any],
        objectives: List[str]
    ) -> Dict[str, Any]:
        """Optimize pricing based on inventory levels and demand forecast"""
        
        # Simplified inventory-based pricing logic
        pricing_adjustments = {}
        
        for product_id, inventory_info in inventory_data.items():
            stock_level = inventory_info.get("stock_level", 0)
            reorder_point = inventory_info.get("reorder_point", 10)
            demand_prediction = demand_forecast.get(product_id, {}).get("predicted_demand", 0)
            
            # Calculate inventory velocity
            if demand_prediction > 0:
                days_of_inventory = stock_level / (demand_prediction / 30)  # Assuming monthly demand
            else:
                days_of_inventory = float('inf')
            
            # Pricing adjustment based on inventory position
            if days_of_inventory < 7:  # Low inventory
                adjustment = 0.10  # Increase price by 10%
                reasoning = "Low inventory - premium pricing"
            elif days_of_inventory > 60:  # High inventory
                adjustment = -0.15  # Decrease price by 15%
                reasoning = "Excess inventory - clearance pricing"
            else:
                adjustment = 0.0
                reasoning = "Normal inventory levels"
            
            pricing_adjustments[product_id] = {
                "adjustment_percentage": adjustment * 100,
                "reasoning": reasoning,
                "inventory_days": days_of_inventory,
                "stock_level": stock_level
            }
        
        return {
            "pricing_adjustments": pricing_adjustments,
            "revenue_impact": sum(abs(adj["adjustment_percentage"]) for adj in pricing_adjustments.values()) / len(pricing_adjustments) if pricing_adjustments else 0,
            "strategy": "inventory_optimization",
            "objectives_addressed": objectives
        }
    
    async def generate_pricing_strategy(
        self, 
        business_objectives: List[str], 
        market_position: str,
        competitive_landscape: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive pricing strategy"""
        
        strategy_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a senior pricing strategist. Create a comprehensive pricing strategy 
            that aligns with business objectives and market position.
            
            Return a detailed JSON strategy:
            {{
                "strategy_name": "string",
                "core_principles": ["principle1", "principle2", ...],
                "pricing_models": {{
                    "primary": "competitive|value_based|cost_plus|dynamic",
                    "secondary": "optional_model"
                }},
                "implementation_plan": [
                    {{
                        "phase": "string",
                        "timeline": "string", 
                        "actions": ["action1", "action2", ...],
                        "success_metrics": ["metric1", "metric2", ...]
                    }}
                ],
                "expected_outcomes": {{
                    "revenue_impact": "percentage_range",
                    "margin_improvement": "percentage_range",
                    "market_share_impact": "description"
                }},
                "risk_mitigation": ["risk1_mitigation", "risk2_mitigation", ...]
            }}
            """),
            ("human", f"""
            Business Objectives: {business_objectives}
            Market Position: {market_position}
            Competitive Landscape: {json.dumps(competitive_landscape, indent=2)}
            """)
        ])
        
        try:
            response = await self.gemini_pro.ainvoke(strategy_prompt.format_messages())
            response_text = response.content
            
            if "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
                
        except Exception as e:
            logger.error(f"Error generating pricing strategy: {e}")
        
        # Fallback strategy
        return {
            "strategy_name": f"{market_position.title()} Market Pricing Strategy",
            "core_principles": [
                "Customer value alignment",
                "Competitive positioning",
                "Profit optimization"
            ],
            "pricing_models": {
                "primary": "competitive",
                "secondary": "value_based"
            },
            "implementation_plan": [
                {
                    "phase": "Analysis and Setup",
                    "timeline": "Weeks 1-2",
                    "actions": [
                        "Conduct market research",
                        "Analyze competitor pricing",
                        "Set up pricing tools"
                    ],
                    "success_metrics": ["Research completion", "Tool deployment"]
                },
                {
                    "phase": "Strategy Implementation", 
                    "timeline": "Weeks 3-6",
                    "actions": [
                        "Deploy new pricing",
                        "Monitor market response",
                        "Adjust based on feedback"
                    ],
                    "success_metrics": ["Revenue growth", "Market share maintenance"]
                }
            ],
            "expected_outcomes": {
                "revenue_impact": "3-7% increase",
                "margin_improvement": "2-5% improvement",
                "market_share_impact": "Maintained or slight increase"
            },
            "risk_mitigation": [
                "Gradual price adjustments",
                "Customer communication strategy",
                "Competitive response monitoring"
            ]
        }
    
    async def analyze_competitor_pricing(
        self, 
        products: List[str], 
        competitors: List[str]
    ) -> Dict[str, Any]:
        """Analyze competitor pricing patterns"""
        
        # In a real implementation, this would integrate with competitor monitoring APIs
        # For now, simulate competitive analysis
        
        competitor_analysis = {
            "competitive_positioning": {},
            "price_gaps": {},
            "opportunities": [],
            "threats": []
        }
        
        for product_id in products:
            # Simulate competitive pricing data
            competitor_analysis["competitive_positioning"][product_id] = {
                "market_position": "mid_market",
                "price_rank": 3,  # Out of 5 competitors
                "price_premium": 5.0,  # 5% above market average
                "competitive_advantage": "product_quality"
            }
            
            competitor_analysis["price_gaps"][product_id] = {
                "gap_to_leader": -15.0,  # 15% below price leader
                "gap_to_average": 5.0,   # 5% above average
                "gap_to_budget": 25.0    # 25% above budget options
            }
        
        competitor_analysis["opportunities"] = [
            "Premium positioning opportunity for high-quality products",
            "Value pricing advantage in competitive segments",
            "Bundle pricing to differentiate from competitors"
        ]
        
        competitor_analysis["threats"] = [
            "Price war risk in commoditized categories",
            "New entrant with aggressive pricing",
            "Market leader's promotional activities"
        ]
        
        return competitor_analysis
    
    # AgentInterface implementation
    async def handle_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Handle incoming A2A message"""
        return await self.a2a_engine.handle_incoming_message(message)
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities"""
        return [AgentCapability.PRICING_OPTIMIZATION]
    
    def get_agent_id(self) -> str:
        """Return agent ID"""
        return self.agent_id

# FastAPI application
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Pricing Optimizer Agent", version="1.0.0")

# Global agent instance
pricing_agent = PricingOptimizerAgent()

@app.on_event("startup")
async def startup():
    """Start agent on application startup"""
    await pricing_agent.start()

@app.on_event("shutdown")
async def shutdown():
    """Stop agent on application shutdown"""
    await pricing_agent.stop()

class PricingRequest(BaseModel):
    """Request model for pricing optimization"""
    products: List[str]
    strategy: str = "dynamic"
    constraints: Dict[str, Any] = {}
    user_context: Dict[str, Any] = {}

@app.post("/optimize-pricing")
async def optimize_pricing(request: PricingRequest):
    """Optimize pricing for given products"""
    payload = {
        "products": request.products,
        "strategy": request.strategy,
        "constraints": request.constraints,
        "user_context": request.user_context
    }
    
    result = await pricing_agent.handle_product_pricing(payload)
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pricing-optimizer-agent",
        "capabilities": [cap.value for cap in pricing_agent.get_capabilities()]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)