#!/bin/bash

# quanBuy Local Testing Script
# Run the platform locally without GCP

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting quanBuy Local Testing Environment${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "Visit: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

# Option to use Gemini API key if available
echo -e "${YELLOW}📝 Gemini API Configuration${NC}"
echo "You can run in two modes:"
echo "1. Mock mode (no API key needed) - uses fallback responses"
echo "2. Real Gemini API mode - requires API key"
echo ""

if [ -z "$GEMINI_API_KEY" ]; then
    echo "No GEMINI_API_KEY found. Running in mock mode."
    echo "To use real Gemini API, run:"
    echo "  export GEMINI_API_KEY='your-api-key'"
    echo ""
    export GEMINI_API_KEY="mock_mode"
else
    echo -e "${GREEN}✅ Using Gemini API key${NC}"
fi

# Start services
echo -e "${YELLOW}🐳 Starting Docker services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 5

# Check service health
echo -e "${YELLOW}🔍 Checking service health...${NC}"
echo ""

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo "❌ Redis is not responding"
fi

# Check Gemini service
if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Gemini service is running${NC}"
else
    echo "❌ Gemini service is not responding"
fi

echo ""
echo -e "${GREEN}🎉 Local environment is ready!${NC}"
echo ""
echo -e "${BLUE}📱 Access Points:${NC}"
echo "  • quanBuy UI: http://localhost:8000/quanbuy.html"
echo "  • Gemini API: http://localhost:8081"
echo "  • API Docs: http://localhost:8081/docs"
echo ""
echo -e "${BLUE}🧪 Test the Gemini Service:${NC}"
echo ""
echo "Mystery Search:"
echo "  curl -X POST http://localhost:8081/mystery-search \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"user_id\": \"test123\", \"search_history\": [\"vintage\", \"bohemian\"]}'"
echo ""
echo "Oracle Search (by feeling):"
echo "  curl -X POST http://localhost:8081/oracle-search \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"user_id\": \"test123\", \"feeling\": \"anxious\"}'"
echo ""
echo -e "${YELLOW}📊 View logs:${NC}"
echo "  docker-compose logs -f geminiservice"
echo ""
echo -e "${YELLOW}🛑 To stop:${NC}"
echo "  docker-compose down"
echo ""
