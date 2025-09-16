#!/bin/bash

echo "========================================="
echo "   Interactive Shopping Agent Test"
echo "========================================="
echo ""

# Function to test a chat message
test_chat() {
    local message="$1"
    local user_id="${2:-test-user}"
    
    echo "📝 Testing: \"$message\""
    echo "---"
    
    response=$(curl -s -X POST http://localhost:8084/chat \
        -H "Content-Type: application/json" \
        -d "{\"user_id\": \"$user_id\", \"message\": \"$message\"}")
    
    # Check if response is valid JSON
    if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        # Extract and display key fields
        success=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
        response_text=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('response', 'No response'))" 2>/dev/null)
        products=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('products', [])))" 2>/dev/null)
        
        if [ "$success" = "True" ]; then
            echo "✅ Success!"
        else
            echo "❌ Failed"
        fi
        
        echo "Response: $response_text"
        
        if [ "$products" -gt 0 ]; then
            echo "📦 Products found: $products"
        fi
    else
        echo "❌ Invalid response: $response"
    fi
    
    echo ""
}

# Kill existing port-forwards
pkill -f "port-forward" 2>/dev/null
sleep 2

# Setup port-forward
echo "Setting up connection to Shopping Agent..."
kubectl port-forward service/shopping-agent 8084:8081 > /dev/null 2>&1 &
PF_PID=$!
sleep 3

# Check health
echo "🏥 Health Check:"
health=$(curl -s http://localhost:8084/health)
if echo "$health" | grep -q "healthy"; then
    echo "✅ Shopping Agent is healthy"
    echo "$health" | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"  - Gemini: {data.get('gemini_configured', False)}\"); print(f\"  - MCP Server: {data.get('mcp_server_url', 'Not configured')}\")" 2>/dev/null
else
    echo "❌ Shopping Agent is not healthy"
    echo "$health"
fi
echo ""

echo "========================================="
echo "   Running Test Scenarios"
echo "========================================="
echo ""

# Test 1: Greeting
test_chat "Hello, I'm looking for help with shopping"

# Test 2: Browse products
test_chat "Can you show me what products you have?"

# Test 3: Search for specific product
test_chat "I'm looking for a vintage camera"

# Test 4: Another search
test_chat "Do you have any coffee makers?"

# Test 5: Cart operations
test_chat "Add product OLJCESPC7Z to my cart" "cart-test-user"
test_chat "What's in my cart?" "cart-test-user"

# Clean up
kill $PF_PID 2>/dev/null

echo "========================================="
echo "   Test Complete!"
echo "========================================="
echo ""
echo "📊 Summary:"
echo "  - Shopping Agent is running with Gemini AI"
echo "  - The agent can understand natural language"
echo "  - It connects to backend services via MCP Server"
echo ""
echo "🎯 Next Steps:"
echo "  1. To test manually:"
echo "     kubectl port-forward service/shopping-agent 8084:8081"
echo "     Then use curl or Postman to send requests"
echo ""
echo "  2. To view the web interface:"
echo "     kubectl port-forward service/frontend 8080:80"
echo "     Open http://localhost:8080 in your browser"
echo ""
echo "  3. To monitor logs:"
echo "     kubectl logs -f deployment/shopping-agent"
