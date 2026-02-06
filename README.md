# Agent Scrum

A multi-agent simulation platform where AI agents self-organize to process work across different domains. Create boards for Software Development, Talent Acquisition, Sales, or Security Operations - each with its own domain-specific agents that collaborate in real-time on a Kanban board.

## Demo

[![Agent Scrum Demo](https://img.youtube.com/vi/iztjBErDY18/maxresdefault.jpg)](https://www.youtube.com/watch?v=iztjBErDY18)

## Quick Start

```bash
make install && make dev
```

Open http://localhost:5173

## What It Does

Create a board from a template, submit work items, and watch domain-specific agents process them through the pipeline:

### Software Development
Submit a PRD and watch agents build it:
1. **Product Owner** parses the PRD and creates user stories
2. **Developer** breaks each story into tasks
3. **Tech Lead** reviews and approves task breakdowns
4. **Developer** writes implementation notes
5. **Code Reviewer** reviews the implementation
6. **QA** creates test scenarios and runs tests

### Talent Acquisition
Submit a job requisition and watch the hiring pipeline:
1. **Sourcing Specialist** finds candidates
2. **Recruiter** screens resumes and conducts phone screens
3. **Interview Coordinator** schedules interviews
4. **Hiring Manager** evaluates candidates
5. **HR Coordinator** prepares offers

### Sales
Submit a lead and watch the deal flow:
1. **Lead Generator** qualifies leads
2. **Account Executive** runs demos and creates proposals
3. **Solutions Engineer** builds POCs
4. **Sales Manager** reviews and approves deals
5. **Contract Specialist** handles negotiations

### CISO / Security Operations
Submit a risk and watch the response:
1. **Threat Analyst** assesses and classifies risks
2. **Security Engineer** implements mitigations
3. **Compliance Officer** audits regulatory alignment
4. **Incident Responder** verifies mitigations
5. **Risk Manager** assesses residual risk

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
make test         # Run 80 backend tests
make docker-up    # Start with Docker
make mcp          # Start MCP server for external tools
make reset        # Reset database
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│              http://localhost:5173                           │
│                                                              │
│   Board Selector ──→ Kanban Board ──→ Agent Chat Panel       │
└────────────────────────┬────────────────────────────────────┘
                         │ REST + WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              LangGraph Swarm Orchestrator               │ │
│  │                                                         │ │
│  │   ┌─────────────────────────────────────────────────┐  │ │
│  │   │  Template-Aware Scanner (scans all boards)      │  │ │
│  │   │  TEMPLATE_WORKFLOWS → dispatch to agents        │  │ │
│  │   └──────────────────────┬──────────────────────────┘  │ │
│  │                          ▼                              │ │
│  │            dynamic_agent_node (universal)                │ │
│  │     Resolves agent_id → role + board_id                 │ │
│  │     Routes to SimulatedAgent with domain context        │ │
│  │                          │                              │ │
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
│  PipelineConfig │ Stories │ Tasks │ Comments │ DynamicAgents │
│    (Boards)     │         │       │          │  (per-board)  │
└─────────────────────────────────────────────────────────────┘
```

## Multi-Board System

Each board is created from a **template** that defines its columns, agents, and workflow rules:

| Template | Item Noun | Agents | Columns |
|----------|-----------|--------|---------|
| **Software Development** | Story | Product Owner, Developer, Tech Lead, Code Reviewer, QA | Backlog, Ready for Breakdown, In Breakdown, Tasks in Review, In Development, In QA, Done |
| **Talent Acquisition** | Candidate | Sourcing Specialist, Recruiter, Hiring Manager, Interview Coordinator, HR Coordinator | Applied, Phone Screen, Interview, Offer, Hired, Rejected |
| **Sales** | Deal | Lead Generator, Account Executive, Sales Manager, Solutions Engineer, Contract Specialist | Lead, Qualified, Proposal, Negotiation, Closed Won, Closed Lost |
| **CISO** | Risk | Threat Analyst, Security Engineer, Compliance Officer, Incident Responder, Risk Manager | Identified, Assessing, Mitigating, Monitoring, Resolved, Accepted |

Agents are board-scoped with IDs like `recruiter_3` (role + board ID). When a board is deleted, its agents are cascade-deleted.

## Workflow Engine

The swarm scanner checks all boards with `agent_automation` enabled every few seconds. For each board, it looks up `TEMPLATE_WORKFLOWS` to determine which column statuses have agent handlers:

```
Board (template_id: "talent_acquisition")
    ↓
TEMPLATE_WORKFLOWS["talent_acquisition"]["story_handlers"]
    "applied"     → (recruiter, screen_resume)
    "phone_screen" → (recruiter, phone_screen)
    "interview"    → (interview_coordinator, schedule_interview)
    "offer"        → (hr_coordinator, prepare_offer)
    ↓
Agent ID = f"{role}_{board_id}" → e.g. "recruiter_3"
    ↓
SimulatedAgent with domain-specific response
    ↓
Move item to next column + post chat message
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
│   │   │   ├── langgraph_agents.py   # Agent definitions + domain simulations
│   │   │   ├── swarm/                # Template-aware swarm orchestrator
│   │   │   ├── tools/                # Database tools + tool registry
│   │   │   └── executor.py           # Agent execution
│   │   ├── api/                      # REST + WebSocket routes
│   │   ├── a2a/                      # A2A protocol router
│   │   ├── mcp/                      # MCP server
│   │   ├── pipeline/                 # Board templates + workflows
│   │   ├── db/                       # SQLAlchemy models + seed
│   │   └── main.py
│   ├── tests/                        # 80 pytest tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/               # React components
│   │   ├── api/                      # API client
│   │   ├── store/                    # Zustand state (story + pipeline)
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

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET/POST /api/boards` | List or create boards |
| `GET/DELETE /api/boards/{id}` | Get or delete a board |
| `GET /api/pipeline/templates` | List available board templates |
| `POST /api/prd` | Submit a PRD / work item |
| `GET/POST /api/stories` | List or create stories |
| `GET/POST /api/tasks` | List or create tasks |
| `GET /api/agents` | List all active agents |
| `GET /api/agents/{id}` | Get agent info |

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
| `board:created` | New board created |
| `board:deleted` | Board deleted |

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

80 tests covering API endpoints, agent workflows, multi-board operations, and database models.

## License

MIT
