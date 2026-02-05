.PHONY: help install dev start stop logs test clean build docker-up docker-down mcp

# Default target
help:
	@echo "Agent Scrum - Multi-Agent Development Simulation"
	@echo ""
	@echo "Quick Start:"
	@echo "  make install    - Install all dependencies"
	@echo "  make dev        - Start development servers (backend + frontend)"
	@echo "  make start      - Same as 'make dev'"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up  - Start with Docker Compose"
	@echo "  make docker-down- Stop Docker containers"
	@echo ""
	@echo "Development:"
	@echo "  make backend    - Start backend only"
	@echo "  make frontend   - Start frontend only"
	@echo "  make test       - Run backend tests"
	@echo "  make mcp        - Start MCP server"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs       - Show backend logs"
	@echo "  make clean      - Remove generated files"
	@echo "  make reset      - Reset database"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Done! Run 'make dev' to start."

# Development mode - starts both servers
dev:
	@echo "Starting Agent Scrum..."
	@./scripts/dev.sh

start: dev

# Start backend only
backend:
	@echo "Starting backend server..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend only
frontend:
	@echo "Starting frontend server..."
	cd frontend && npm run dev

# Run tests
test:
	@echo "Running tests..."
	cd backend && python -m pytest tests/ -v

# Start MCP server
mcp:
	@echo "Starting MCP server..."
	cd backend && python -m app.mcp.task_server

# Docker commands
docker-up:
	@echo "Starting with Docker..."
	docker-compose up -d
	@echo "Frontend: http://localhost:5173"
	@echo "Backend:  http://localhost:8000"

docker-down:
	docker-compose down

docker-dev:
	docker-compose --profile dev up

docker-build:
	docker-compose build

# Logs
logs:
	@tail -f backend/*.log 2>/dev/null || echo "No log files found. Start the server first."

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf backend/__pycache__ backend/**/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf backend/data/*.db
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
	@echo "Done!"

# Reset database
reset:
	@echo "Resetting database..."
	rm -f backend/data/agent_scrum.db
	@echo "Database reset. It will be recreated on next start."
