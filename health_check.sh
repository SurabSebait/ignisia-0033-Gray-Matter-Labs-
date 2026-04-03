#!/bin/bash
# Health Check Script for FastAPI RAG Deployment
# Usage: bash health_check.sh [host] [port]

HOST=${1:-localhost}
PORT=${2:-8000}
BASE_URL="http://$HOST:$PORT"

echo "🔍 FastAPI RAG Health Check"
echo "============================"
echo "Host: $HOST"
echo "Port: $PORT"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Health Endpoint
echo "1️⃣  Testing /health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ Health check passed${NC} (HTTP $HEALTH_RESPONSE)"
else
    echo -e "${RED}✗ Health check failed${NC} (HTTP $HEALTH_RESPONSE)"
    exit 1
fi

# Test 2: Root Endpoint
echo ""
echo "2️⃣  Testing / root endpoint..."
ROOT_RESPONSE=$(curl -s "$BASE_URL/" | jq . 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Root endpoint working${NC}"
    echo "Response: $(echo $ROOT_RESPONSE | jq -c '.version')"
else
    echo -e "${RED}✗ Root endpoint failed${NC}"
fi

# Test 3: Docs Endpoint
echo ""
echo "3️⃣  Testing /docs (Swagger UI)..."
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs")
if [ "$DOCS_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ API Documentation available${NC} (HTTP $DOCS_RESPONSE)"
    echo "   Access at: $BASE_URL/docs"
else
    echo -e "${RED}✗ API Documentation not available${NC} (HTTP $DOCS_RESPONSE)"
fi

# Test 4: Query Endpoint (with sample query)
echo ""
echo "4️⃣  Testing /api/query endpoint..."
QUERY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/query" \
    -H "Content-Type: application/json" \
    -d '{"question": "test"}' \
    -w "\n%{http_code}" | tail -1)

if [ "$QUERY_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ Query endpoint working${NC} (HTTP $QUERY_RESPONSE)"
else
    echo -e "${YELLOW}⚠ Query endpoint returned${NC} (HTTP $QUERY_RESPONSE)"
    echo "   This is normal if RAG system is still initializing"
fi

# Test 5: System Checks
echo ""
echo "5️⃣  System Checks..."

# Check if process is running (if local)
if [ "$HOST" = "localhost" ] || [ "$HOST" = "127.0.0.1" ]; then
    if pgrep -f "gunicorn.*main:app" > /dev/null; then
        echo -e "${GREEN}✓ Gunicorn process running${NC}"
    else
        echo -e "${RED}✗ Gunicorn process not found${NC}"
    fi
    
    if pgrep -f "nginx" > /dev/null; then
        echo -e "${GREEN}✓ Nginx process running${NC}"
    else
        echo -e "${YELLOW}⚠ Nginx process not running${NC}"
    fi
fi

# Test 6: Connection Test
echo ""
echo "6️⃣  Connection Latency..."
START_TIME=$(date +%s%N)
curl -s -o /dev/null "$BASE_URL/health"
END_TIME=$(date +%s%N)
LATENCY=$((($END_TIME - $START_TIME) / 1000000))
echo -e "   Response time: ${GREEN}${LATENCY}ms${NC}"

echo ""
echo "============================"
echo -e "${GREEN}✓ Health check complete!${NC}"
echo ""
echo "📊 Monitoring:"
echo "   - View logs: tail -f /var/log/fastapi-rag.out.log"
echo "   - Check status: sudo supervisorctl status fastapi-rag"
echo "   - System resources: htop"
echo ""
