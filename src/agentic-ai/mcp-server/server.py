#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server for Online Boutique Microservices
Provides secure API access for AI agents to interact with existing microservices
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any
import grpc
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
sys.path.append('../../../protos')

# Import generated gRPC stubs
from genproto import demo_pb2, demo_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPResource(BaseModel):
    uri: str
    name: str
    description: str
    methods: List[str]

class MCPTool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class MCPRequest(BaseModel):
    tool: str
    parameters: Dict[str, Any]

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class OnlineBoutiqueMCPServer:
    """MCP Server that provides controlled access to Online Boutique microservices"""
    
    def __init__(self):
        self.app = FastAPI(title="Online Boutique MCP Server", version="1.0.0")
        self.setup_cors()
        self.setup_routes()
        self.grpc_channels = {}
        self.grpc_stubs = {}
        self.initialize_grpc_connections()
        
    def setup_cors(self):
        """Configure CORS for cross-origin requests"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def initialize_grpc_connections(self):
        """Initialize gRPC connections to microservices"""
        microservices = {
            'cartservice': os.getenv('CART_SERVICE_ADDR', 'cartservice:7070'),
            'productcatalogservice': os.getenv('PRODUCT_CATALOG_SERVICE_ADDR', 'productcatalogservice:3550'),
            'currencyservice': os.getenv('CURRENCY_SERVICE_ADDR', 'currencyservice:7000'),
            'recommendationservice': os.getenv('RECOMMENDATION_SERVICE_ADDR', 'recommendationservice:8080'),
            'shippingservice': os.getenv('SHIPPING_SERVICE_ADDR', 'shippingservice:50051'),
            'checkoutservice': os.getenv('CHECKOUT_SERVICE_ADDR', 'checkoutservice:5050'),
            'paymentservice': os.getenv('PAYMENT_SERVICE_ADDR', 'paymentservice:50051'),
            'emailservice': os.getenv('EMAIL_SERVICE_ADDR', 'emailservice:8080'),
            'adservice': os.getenv('AD_SERVICE_ADDR', 'adservice:9555')
        }
        
        for service_name, address in microservices.items():
            try:
                channel = grpc.aio.insecure_channel(address)
                self.grpc_channels[service_name] = channel
                
                # Create appropriate stub for each service
                if service_name == 'cartservice':
                    self.grpc_stubs[service_name] = demo_pb2_grpc.CartServiceStub(channel)
                elif service_name == 'productcatalogservice':
                    self.grpc_stubs[service_name] = demo_pb2_grpc.ProductCatalogServiceStub(channel)
                elif service_name == 'currencyservice':
                    self.grpc_stubs[service_name] = demo_pb2_grpc.CurrencyServiceStub(channel)
                elif service_name == 'recommendationservice':
                    self.grpc_stubs[service_name] = demo_pb2_grpc.RecommendationServiceStub(channel)
                elif service_name == 'shippingservice':
                    self.grpc_stubs[service_name] = demo_pb2_grpc.ShippingServiceStub(channel)
                elif service_name == 'checkoutservice':
                    self.grpc_stubs[service_name] = demo_pb2_grpc.CheckoutServiceStub(channel)
                elif service_name == 'paymentservice':
                    self.grpc_stubs[service_name] = demo_pb2_grpc.PaymentServiceStub(channel)
                elif service_name == 'emailservice':
                    self.grpc_stubs[service_name] = demo_pb2_grpc.EmailServiceStub(channel)
                elif service_name == 'adservice':
                    self.grpc_stubs[service_name] = demo_pb2_grpc.AdServiceStub(channel)
                    
                logger.info(f"Connected to {service_name} at {address}")
            except Exception as e:
                logger.error(f"Failed to connect to {service_name}: {e}")
    
    def setup_routes(self):
        """Setup MCP API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy"}
        
        @self.app.get("/mcp/resources")
        async def get_resources() -> List[MCPResource]:
            """Return available MCP resources"""
            return [
                MCPResource(
                    uri="boutique://cart/{user_id}",
                    name="User Shopping Cart",
                    description="Access and modify user shopping cart",
                    methods=["GET", "POST", "DELETE"]
                ),
                MCPResource(
                    uri="boutique://products/search",
                    name="Product Search",
                    description="Search products in catalog",
                    methods=["GET"]
                ),
                MCPResource(
                    uri="boutique://products/{product_id}",
                    name="Product Details",
                    description="Get detailed product information",
                    methods=["GET"]
                ),
                MCPResource(
                    uri="boutique://recommendations/{user_id}",
                    name="Product Recommendations",
                    description="Get personalized product recommendations",
                    methods=["GET"]
                ),
                MCPResource(
                    uri="boutique://shipping/quote",
                    name="Shipping Quote",
                    description="Get shipping cost estimate",
                    methods=["POST"]
                ),
                MCPResource(
                    uri="boutique://currency/convert",
                    name="Currency Conversion",
                    description="Convert between currencies",
                    methods=["POST"]
                )
            ]
        
        @self.app.get("/mcp/tools")
        async def get_tools() -> List[MCPTool]:
            """Return available MCP tools"""
            return [
                MCPTool(
                    name="add_to_cart",
                    description="Add item to user's shopping cart",
                    parameters={
                        "user_id": {"type": "string", "description": "User identifier"},
                        "product_id": {"type": "string", "description": "Product identifier"},
                        "quantity": {"type": "integer", "description": "Quantity to add"}
                    }
                ),
                MCPTool(
                    name="get_cart",
                    description="Retrieve user's shopping cart",
                    parameters={
                        "user_id": {"type": "string", "description": "User identifier"}
                    }
                ),
                MCPTool(
                    name="search_products",
                    description="Search for products",
                    parameters={
                        "query": {"type": "string", "description": "Search query"}
                    }
                ),
                MCPTool(
                    name="get_product",
                    description="Get product details",
                    parameters={
                        "product_id": {"type": "string", "description": "Product identifier"}
                    }
                ),
                MCPTool(
                    name="get_recommendations",
                    description="Get product recommendations",
                    parameters={
                        "user_id": {"type": "string", "description": "User identifier"},
                        "product_ids": {"type": "array", "description": "Current cart product IDs"}
                    }
                ),
                MCPTool(
                    name="get_shipping_quote",
                    description="Get shipping cost estimate",
                    parameters={
                        "address": {"type": "object", "description": "Shipping address"},
                        "items": {"type": "array", "description": "Cart items"}
                    }
                ),
                MCPTool(
                    name="convert_currency",
                    description="Convert currency amounts",
                    parameters={
                        "from_amount": {"type": "object", "description": "Source amount with currency"},
                        "to_currency": {"type": "string", "description": "Target currency code"}
                    }
                )
            ]
        
        @self.app.post("/mcp/call")
        async def call_tool(request: MCPRequest) -> MCPResponse:
            """Execute MCP tool call"""
            try:
                if request.tool == "add_to_cart":
                    return await self.add_to_cart(request.parameters)
                elif request.tool == "get_cart":
                    return await self.get_cart(request.parameters)
                elif request.tool == "search_products":
                    return await self.search_products(request.parameters)
                elif request.tool == "get_product":
                    return await self.get_product(request.parameters)
                elif request.tool == "get_recommendations":
                    return await self.get_recommendations(request.parameters)
                elif request.tool == "get_shipping_quote":
                    return await self.get_shipping_quote(request.parameters)
                elif request.tool == "convert_currency":
                    return await self.convert_currency(request.parameters)
                else:
                    return MCPResponse(success=False, error=f"Unknown tool: {request.tool}")
            except Exception as e:
                logger.error(f"Error executing tool {request.tool}: {e}")
                return MCPResponse(success=False, error=str(e))
    
    async def add_to_cart(self, params: Dict[str, Any]) -> MCPResponse:
        """Add item to cart via CartService"""
        try:
            cart_request = demo_pb2.AddItemRequest(
                user_id=params["user_id"],
                item=demo_pb2.CartItem(
                    product_id=params["product_id"],
                    quantity=params["quantity"]
                )
            )
            
            await self.grpc_stubs['cartservice'].AddItem(cart_request)
            return MCPResponse(success=True, data={"message": "Item added to cart"})
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def get_cart(self, params: Dict[str, Any]) -> MCPResponse:
        """Get cart contents via CartService"""
        try:
            cart_request = demo_pb2.GetCartRequest(user_id=params["user_id"])
            cart_response = await self.grpc_stubs['cartservice'].GetCart(cart_request)
            
            cart_data = {
                "user_id": cart_response.user_id,
                "items": [
                    {"product_id": item.product_id, "quantity": item.quantity}
                    for item in cart_response.items
                ]
            }
            
            return MCPResponse(success=True, data=cart_data)
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def search_products(self, params: Dict[str, Any]) -> MCPResponse:
        """Search products via ProductCatalogService"""
        try:
            search_request = demo_pb2.SearchProductsRequest(query=params["query"])
            search_response = await self.grpc_stubs['productcatalogservice'].SearchProducts(search_request)
            
            products = []
            for product in search_response.results:
                products.append({
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "picture": product.picture,
                    "price_usd": {
                        "currency_code": product.price_usd.currency_code,
                        "units": product.price_usd.units,
                        "nanos": product.price_usd.nanos
                    },
                    "categories": list(product.categories)
                })
            
            return MCPResponse(success=True, data={"products": products})
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def get_product(self, params: Dict[str, Any]) -> MCPResponse:
        """Get product details via ProductCatalogService"""
        try:
            product_request = demo_pb2.GetProductRequest(id=params["product_id"])
            product = await self.grpc_stubs['productcatalogservice'].GetProduct(product_request)
            
            product_data = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "picture": product.picture,
                "price_usd": {
                    "currency_code": product.price_usd.currency_code,
                    "units": product.price_usd.units,
                    "nanos": product.price_usd.nanos
                },
                "categories": list(product.categories)
            }
            
            return MCPResponse(success=True, data=product_data)
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def get_recommendations(self, params: Dict[str, Any]) -> MCPResponse:
        """Get recommendations via RecommendationService"""
        try:
            rec_request = demo_pb2.ListRecommendationsRequest(
                user_id=params["user_id"],
                product_ids=params.get("product_ids", [])
            )
            rec_response = await self.grpc_stubs['recommendationservice'].ListRecommendations(rec_request)
            
            return MCPResponse(success=True, data={"product_ids": list(rec_response.product_ids)})
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def get_shipping_quote(self, params: Dict[str, Any]) -> MCPResponse:
        """Get shipping quote via ShippingService"""
        try:
            address = demo_pb2.Address(
                street_address=params["address"]["street_address"],
                city=params["address"]["city"],
                state=params["address"]["state"],
                country=params["address"]["country"],
                zip_code=params["address"]["zip_code"]
            )
            
            items = [
                demo_pb2.CartItem(product_id=item["product_id"], quantity=item["quantity"])
                for item in params["items"]
            ]
            
            quote_request = demo_pb2.GetQuoteRequest(address=address, items=items)
            quote_response = await self.grpc_stubs['shippingservice'].GetQuote(quote_request)
            
            return MCPResponse(success=True, data={
                "cost_usd": {
                    "currency_code": quote_response.cost_usd.currency_code,
                    "units": quote_response.cost_usd.units,
                    "nanos": quote_response.cost_usd.nanos
                }
            })
        except Exception as e:
            return MCPResponse(success=False, error=str(e))
    
    async def convert_currency(self, params: Dict[str, Any]) -> MCPResponse:
        """Convert currency via CurrencyService"""
        try:
            from_money = demo_pb2.Money(
                currency_code=params["from_amount"]["currency_code"],
                units=params["from_amount"]["units"],
                nanos=params["from_amount"]["nanos"]
            )
            
            conversion_request = demo_pb2.CurrencyConversionRequest(
                from_currency=from_money,
                to_code=params["to_currency"]
            )
            
            converted_money = await self.grpc_stubs['currencyservice'].Convert(conversion_request)
            
            return MCPResponse(success=True, data={
                "currency_code": converted_money.currency_code,
                "units": converted_money.units,
                "nanos": converted_money.nanos
            })
        except Exception as e:
            return MCPResponse(success=False, error=str(e))

# Create MCP server instance
mcp_server = OnlineBoutiqueMCPServer()
app = mcp_server.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
