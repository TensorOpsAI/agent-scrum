# Agent Scrum

A multi-agent simulation of an Agile development team. AI agents collaborate to process requirements, break down stories, review code, and run tests - all visible in real-time on a Kanban board.

## Demo

https://github.com/TensorOpsAI/agent-scrum/raw/main/AgentScrum.mp4

## Quick Start

```bash
make install && make dev
```

Open http://localhost:5173

## What It Does

Submit a PRD (Product Requirements Document) and watch AI agents work through it:

1. **Product Owner** parses the PRD and creates multiple user stories
2. **Developer** breaks each story into tasks
3. **Tech Lead** reviews and approves task breakdowns
4. **Developer** writes implementation notes
5. **Code Reviewer** reviews the implementation
6. **QA** creates test scenarios and runs tests
7. Stories automatically move to **Done** when complete

Everything happens in real-time with WebSocket updates - no page refresh needed.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agents | LangGraph + LangChain |
| Backend | FastAPI, SQLAlchemy (async), SQLite |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Real-time | WebSocket |
| AI | Google Gemini API (or simulation mode) |
| Protocol | A2A (Agent-to-Agent) + MCP |

## Commands

```bash
make install      # Install Python + Node dependencies
make dev          # Start backend + frontend
make test         # Run 72 backend tests
make docker-up    # Start with Docker
make mcp          # Start MCP server for external tools
make reset        # Reset database
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│              http://localhost:5173                           │
└────────────────────────┬────────────────────────────────────┘
                         │ REST + WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              LangGraph Swarm Orchestrator               │ │
│  │                                                         │ │
│  │   Product     Tech                    Code              │ │
│  │    Owner     Lead     Developer     Reviewer     QA     │ │
│  │      │         │          │            │          │     │ │
│  │      └─────────┴──────────┴────────────┴──────────┘     │ │
│  │                         │                                │ │
│  │              A2A Router (chat messages)                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                         │                                    │
│  ┌──────────────┐  ┌────┴─────┐  ┌─────────────────────┐   │
│  │  REST API    │  │ WebSocket │  │    MCP Server       │   │
│  └──────────────┘  └──────────┘  └─────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    SQLite Database                           │
│   Stories │ Tasks │ Comments │ AgentMessages │ DynamicAgents │
└─────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Role |
|-------|------|
| **Product Owner** | Parses PRDs into multiple user stories (agile-focused, defines WHAT not HOW) |
| **Developer** | Breaks stories into tasks, writes implementation notes |
| **Tech Lead** | Reviews task breakdowns, provides technical guidance |
| **Code Reviewer** | Reviews implementation, approves or requests changes |
| **QA** | Creates test scenarios, runs tests, closes completed stories |

## Workflow

```
PRD Submitted
    ↓
Product Owner creates stories ──→ READY_FOR_BREAKDOWN
    ↓
Developer breaks down story ────→ IN_BREAKDOWN → TASKS_IN_REVIEW
    ↓
Tech Lead reviews tasks ────────→ IN_DEVELOPMENT
    ↓
Developer implements ───────────→ CODE_REVIEW
    ↓
Code Reviewer approves ─────────→ READY_FOR_QA → IN_QA
    ↓
QA tests and closes ────────────→ DONE
```

## Configuration

Create `backend/.env`:

```bash
GEMINI_API_KEY=your-key    # Optional - for real LLM responses
SIMULATE_MODE=true         # Default - uses mock agent responses
```

Get a Gemini API key at https://aistudio.google.com/apikey

## Settings UI

Click the gear icon to access settings:
- **Start/Stop/Pause Swarm** - Control agent automation
- **API Key** - Add or clear your Gemini API key
- **Simulation Mode** - Toggle mock responses
- **Reset Data** - Clear all stories and tasks

## MCP Integration

The task system is exposed via Model Context Protocol for use with Claude Desktop or other MCP clients:

```bash
make mcp
```

Add to your MCP config:
```json
{
  "mcpServers": {
    "agent-scrum-tasks": {
      "command": "python",
      "args": ["-m", "app.mcp.task_server"],
      "cwd": "/path/to/agent-scrum/backend"
    }
  }
}
```

**14 MCP Tools Available:**
- `get_story`, `create_story`, `update_story_status`, `list_stories_by_status`
- `get_task`, `create_task`, `update_task_status`, `get_tasks_for_story`
- `update_task_implementation`, `update_task_test_scenarios`, `list_tasks_by_status`
- `add_comment`, `get_task_comments`, `get_board_summary`

## Project Structure

```
agent-scrum/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── langgraph_agents.py   # Agent definitions (LangGraph)
│   │   │   ├── swarm/                # Swarm orchestrator
│   │   │   ├── tools/                # Database tools
│   │   │   └── executor.py           # Agent execution
│   │   ├── api/                      # REST + WebSocket routes
│   │   ├── a2a/                      # A2A protocol router
│   │   ├── mcp/                      # MCP server
│   │   ├── db/                       # SQLAlchemy models
│   │   └── main.py
│   ├── tests/                        # 72 pytest tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/               # React components
│   │   ├── api/                      # API client
│   │   ├── store/                    # Zustand state
│   │   └── hooks/                    # WebSocket hook
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── Makefile
└── README.md
```

## API

- **REST API**: http://localhost:8000/docs (Swagger UI)
- **WebSocket**: `ws://localhost:8000/ws`
- **Health**: http://localhost:8000/health

### WebSocket Events

| Event | Description |
|-------|-------------|
| `story:created` | New story added |
| `story:updated` | Story status/content changed |
| `task:created` | New task added |
| `task:updated` | Task status/content changed |
| `agent:status_changed` | Agent started/stopped work |
| `agent:chat` | Agent sent a message |
| `swarm:status` | Swarm started/stopped/paused |

## Docker

```bash
# Production
docker-compose up -d

# Development (hot reload)
docker-compose --profile dev up
```

## Testing

```bash
make test                    # Run all tests
cd backend && pytest -v      # Verbose output
```

72 tests covering API endpoints, agent workflows, and database operations.

## License

MIT
