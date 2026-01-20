#!/bin/bash
set -e

echo "=============================="
echo "Redeploy Backend + Frontend"
echo "=============================="

PROJECT_DIR="$HOME/ai_powered_form_agent/src"

BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

BACKEND_IMAGE="ai-form-backend"
FRONTEND_IMAGE="ai-form-frontend"

BACKEND_CONTAINER="ai-form-backend"
FRONTEND_CONTAINER="ai-form-frontend"

BACKEND_PORT=8000
FRONTEND_PORT=8501

echo ""
echo ">>> Going to project dir: $PROJECT_DIR"
cd "$PROJECT_DIR"

echo ""
echo ">>> Stopping old containers (if running)..."
docker stop "$BACKEND_CONTAINER" 2>/dev/null || true
docker stop "$FRONTEND_CONTAINER" 2>/dev/null || true

echo ""
echo ">>> Removing old containers (if exist)..."
docker rm "$BACKEND_CONTAINER" 2>/dev/null || true
docker rm "$FRONTEND_CONTAINER" 2>/dev/null || true

echo ""
echo ">>> Building backend image..."
cd "$BACKEND_DIR"
docker build -t "$BACKEND_IMAGE" .

echo ""
echo ">>> Running backend container..."
docker run -d --name "$BACKEND_CONTAINER" \
  --restart unless-stopped \
  -p ${BACKEND_PORT}:8000 \
  --env-file "$BACKEND_DIR/.env" \
  "$BACKEND_IMAGE"

echo ""
echo ">>> Building frontend image..."
cd "$FRONTEND_DIR"
docker build -t "$FRONTEND_IMAGE" .

echo ""
echo ">>> Running frontend container..."
docker run -d --name "$FRONTEND_CONTAINER" \
  --restart unless-stopped \
  -p ${FRONTEND_PORT}:8501 \
  -e API_BASE_URL="http://34.202.126.236/api" \
  "$FRONTEND_IMAGE"

echo ""
echo ">>> Running containers:"
docker ps | grep -E "ai-form-backend|ai-form-frontend" || true

echo ""
echo ">>> Quick health checks:"
echo "Backend status:"
curl -s http://127.0.0.1:${BACKEND_PORT}/status || true
echo ""
echo "Frontend (should return HTML):"
curl -I http://127.0.0.1:${FRONTEND_PORT} | head -n 5 || true

echo ""
echo "DONE ✅"

docker logs -f ai-form-backend 
