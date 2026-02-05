#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       🤖 Agent Scrum - Dev Server         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"

if ! command -v python &> /dev/null; then
    echo -e "${RED}Python not found. Please install Python 3.11+${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm not found. Please install Node.js 18+${NC}"
    exit 1
fi

# Start backend
echo -e "\n${GREEN}Starting backend server...${NC}"
cd "$BACKEND_DIR"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}Backend ready!${NC}"
        break
    fi
    sleep 1
done

# Start frontend
echo -e "\n${GREEN}Starting frontend server...${NC}"
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo -e "\n${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}  ✓ Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}  ✓ API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to stop${NC}\n"

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID
