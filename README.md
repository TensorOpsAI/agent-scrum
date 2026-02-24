# Agent Scrum

A multi-agent simulation platform where AI agents self-organize to process work across different domains. Create boards for Publishing, Software Development, Talent Acquisition, Sales, or Security Operations - each with its own domain-specific agents that collaborate in real-time on a Kanban board.

[![Agent Scrum Demo](https://img.youtube.com/vi/iztjBErDY18/maxresdefault.jpg)](https://www.youtube.com/watch?v=iztjBErDY18)

## Quick Start

```bash
make install && make dev
```

Open http://localhost:5173

## How It Works

Agent Scrum is built on three core ideas: a **LangGraph swarm** that continuously scans for work, an **A2A protocol** that lets agents talk to each other, and an **MCP server** that exposes the board to external tools. Here's how they fit together.

### The Swarm Loop

When you click "Start Swarm", a background loop begins:

```
every 3-6 seconds:
    for each board where agent_automation is enabled:
        look up TEMPLATE_WORKFLOWS[board.template_id]
        for each (status -> agent_role, action) mapping:
            find items stuck in that status
            dispatch the right agent to handle them
```

This is implemented as a [LangGraph StateGraph](https://langchain-ai.github.io/langgraph/) with two nodes:

1. **Router node** - scans all boards, finds stuck items, picks the next agent
2. **Agent node** - invokes the selected agent, which does its work and moves the item forward

The graph loops: `router -> agent -> router -> agent -> ... -> end` (when no more work is found or max iterations hit). Then the monitor sleeps 3-6 seconds and runs again.

```
┌──────────┐     has work?     ┌───────────────────┐
│  Router  │ ───── yes ──────→ │ dynamic_agent_node │
│  (scan)  │                   │  (invoke agent)    │
└──────────┘                   └────────┬───────────┘
     ↑                                  │
     └────────── more work? ────────────┘
                    no → END
```

### Agent Dispatch

Each board template defines which agent handles which column transition. For example, the Publisher template (default):

| When item reaches status | Agent dispatched | Action |
|--------------------------|-----------------|--------|
| `writing` | Journalist | Write article |
| `editing` | Editor | Review article |
| `creatives` | Creative Director | Create visuals |
| `ready_to_publish` | Publisher | Publish content |

Or the Software Development template:

| When item reaches status | Agent dispatched | Action |
|--------------------------|-----------------|--------|
| `ready_for_breakdown` | Developer | Break story into tasks |
| `tasks_in_review` | Tech Lead | Review task breakdown |
| `ready_for_development` | Developer | Write implementation notes |
| `code_review` | Code Reviewer | Review implementation |
| `ready_for_qa` | QA | Create test scenarios |

Agents are board-scoped: `developer_1` is the Developer on board 1, `recruiter_3` is the Recruiter on board 3. The swarm resolves `agent_id -> role + board_id` to dispatch the right agent.

### A2A Protocol (Agent-to-Agent)

Agents communicate through the [A2A protocol](https://google.github.io/A2A/), Google's open standard for agent interoperability. The implementation follows the JSON-RPC 2.0 spec:

**How agents talk to each other:**

When the swarm dispatches an agent, it doesn't call the agent directly. Instead, it sends an A2A message through the router:

```
Swarm ──→ a2a_router.send_to_agent(
              from_agent="scrum_master",
              to_agent="developer_1",
              message="Process story #5: User Authentication",
              context={story_id: 5, board_id: 1}
          )
```

The A2A router then:
1. Records the outgoing message in `AgentMessage` table (visible in chat)
2. Broadcasts it via WebSocket (appears in the UI chat panel in real-time)
3. Calls `executor.execute_agent()` which invokes the LangGraph agent
4. Records the agent's response as a reply message
5. Returns an `A2ATask` object with state (submitted/working/completed/failed)

**JSON-RPC methods implemented:**

| Method | Description |
|--------|-------------|
| `tasks/send` | Send a message to create or continue an A2A task |
| `tasks/get` | Retrieve a task's current state and message history |
| `tasks/cancel` | Cancel a running task |

**Agent discovery:**

Each agent has an A2A Agent Card accessible at `/api/agents/{id}` containing:
- Name, description, capabilities
- Skills list (what the agent can do)
- Status (idle/working)

The Agent Registry (`a2a/registry.py`) tracks all agents and their current state, enabling agents to discover each other's capabilities at runtime.

**Chat visibility:**

Every A2A message is persisted to the database and broadcast via WebSocket, so the UI chat panel shows the full conversation between agents as they work. You can see agents handing off work, reporting results, and coordinating in real-time.

### MCP Integration (Model Context Protocol)

The board is exposed as an [MCP server](https://modelcontextprotocol.io/) so external AI tools (Claude Desktop, Cursor, etc.) can read and manipulate the board programmatically.

```
┌──────────────────┐         stdio          ┌───────────────────┐
│  Claude Desktop  │ ◄────────────────────► │  MCP Task Server  │
│  or any MCP      │    JSON-RPC over       │  (14 tools)       │
│  client          │    stdin/stdout        │                   │
└──────────────────┘                        └─────────┬─────────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │ SQLite Database│
                                              └───────────────┘
```

Start the MCP server:
```bash
make mcp
```

Add to your MCP client config (e.g., Claude Desktop `claude_desktop_config.json`):
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

**14 MCP tools available:**

| Tool | Description |
|------|-------------|
| `get_story` | Fetch a story by ID |
| `create_story` | Create a new story on a board |
| `update_story_status` | Move a story to a new column |
| `list_stories_by_status` | List all stories in a given status |
| `get_task` | Fetch a task by ID |
| `create_task` | Create a task under a story |
| `update_task_status` | Move a task to a new status |
| `get_tasks_for_story` | Get all tasks for a story |
| `update_task_implementation` | Write implementation notes on a task |
| `update_task_test_scenarios` | Write test scenarios on a task |
| `list_tasks_by_status` | List tasks by status |
| `add_comment` | Add a comment to a story or task |
| `get_task_comments` | Get all comments on a task |
| `get_board_summary` | Get a summary of all boards and their items |

This means you can ask Claude: *"Look at the scrum board, find any stories stuck in code review, and summarize what's blocking them"* - and it will use the MCP tools to query your board directly.

### Simulation Mode

By default, agents run in **simulation mode** - no API key needed. Simulated agents:

1. Sleep 2-4 seconds (simulated work time)
2. Use domain-specific response templates (e.g., a Recruiter says *"Reviewed candidate resume. 5 years experience. Recommending for phone screen."*)
3. Actually create/modify records in the database (stories, tasks, status transitions)
4. Post chat messages through A2A so you can watch the conversation

With a Gemini API key, agents use real LLM calls via LangChain + LangGraph ReAct agents with database tools.

---

## Board Templates

Each board is created from a template that defines its columns, agents, and workflow rules:

| Template | Items | Agents |
|----------|-------|--------|
| **Publisher** (default) | Articles + Sections | News Curator, Journalist, Editor, Creative Director, Publisher, Editor-in-Chief |
| **Software Development** | Stories + Tasks | Product Owner, Developer, Tech Lead, Code Reviewer, QA, Scrum Master |
| **Talent Acquisition** | Candidates | Sourcing Specialist, Recruiter, Hiring Manager, Interview Coordinator, HR Coordinator |
| **Sales** | Deals | Lead Generator, Account Executive, Sales Manager, Solutions Engineer, Contract Specialist |
| **CISO** | Risks | Threat Analyst, Security Engineer, Compliance Officer, Incident Responder, Risk Manager |

### Publisher (Default)
Click "Generate Articles" to auto-generate news briefs, then start the swarm:
1. **News Curator** scans news sources, selects newsworthy items, and creates articles
2. **Journalist** writes articles from curated news items
3. **Editor** reviews articles for quality, accuracy, and tone
4. **Creative Director** selects or generates visuals and thumbnails
5. **Publisher** formats content, optimizes SEO, and publishes
6. **Editor-in-Chief** oversees the pipeline and assigns stories

Pipeline: Inbox → Writing → Editing → Creatives → Ready to Publish → Published

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

---

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
│  │              LangGraph Swarm (StateGraph)               │ │
│  │                                                         │ │
│  │   Router ──→ scan_board() ──→ TEMPLATE_WORKFLOWS        │ │
│  │     │                                                   │ │
│  │     ▼                                                   │ │
│  │   dynamic_agent_node ──→ A2A Router ──→ Executor        │ │
│  │     │                       │                           │ │
│  │     │                  record message                   │ │
│  │     │                  broadcast WS                     │ │
│  │     │                       │                           │ │
│  │     └───────────────────────┘                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                         │                                    │
│  ┌──────────────┐  ┌────┴─────┐  ┌─────────────────────┐   │
│  │  REST API    │  │ WebSocket │  │   MCP Server (14)   │   │
│  │  /api/*      │  │ /ws      │  │   stdio transport    │   │
│  └──────────────┘  └──────────┘  └─────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    SQLite Database                           │
│  PipelineConfig │ Stories │ Tasks │ Comments │ DynamicAgents │
│  AgentMessages  │         │       │          │  (per-board)  │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent orchestration | LangGraph StateGraph + LangChain |
| Agent communication | A2A protocol (JSON-RPC 2.0) |
| External tool access | MCP (Model Context Protocol) |
| Backend | FastAPI, SQLAlchemy (async), SQLite |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Real-time | WebSocket |
| AI | Google Gemini API (or simulation mode) |

## Running

```bash
# First time setup
make install          # Install Python + Node dependencies

# Start the app
make dev              # Start backend (port 8000) + frontend (port 5173)

# Open http://localhost:5173

# Other commands
make test             # Run backend tests
make docker-up        # Start with Docker
make mcp              # Start MCP server for external tools
make reset            # Delete database and re-seed fresh
make backend          # Start backend only
make frontend         # Start frontend only
```

To switch the default board template, delete the database and restart:

```bash
make reset && make dev
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

## Project Structure

```
agent-scrum/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── langgraph_agents.py   # Agent definitions + domain simulations
│   │   │   ├── swarm/graph.py        # LangGraph StateGraph (router + agent nodes)
│   │   │   ├── swarm/state.py        # Swarm state schema
│   │   │   ├── tools/db_tools.py     # LangChain tools for DB operations
│   │   │   ├── tools/registry.py     # Tool basket (Publishing, HR, Sales, InfoSec, Dev)
│   │   │   └── executor.py           # Agent execution with capacity limits
│   │   ├── a2a/
│   │   │   ├── protocol.py           # JSON-RPC 2.0 handler (tasks/send, get, cancel)
│   │   │   ├── router.py             # A2A message routing + chat recording
│   │   │   └── registry.py           # Agent discovery (cards, skills, status)
│   │   ├── mcp/
│   │   │   ├── task_server.py         # MCP server (14 tools, stdio transport)
│   │   │   └── client.py             # MCP client for connecting to the server
│   │   ├── api/                      # REST + WebSocket routes
│   │   ├── pipeline/
│   │   │   └── templates.py          # Board templates + TEMPLATE_WORKFLOWS
│   │   ├── workflow/
│   │   │   ├── orchestrator.py       # Status transition handlers
│   │   │   └── triggers.py           # Event-based triggers (PRD submit, etc.)
│   │   ├── db/
│   │   │   ├── models.py             # SQLAlchemy models
│   │   │   ├── seed.py               # Per-board agent seeding
│   │   │   └── database.py           # Async engine + session
│   │   └── main.py
│   ├── tests/                        # 80 pytest tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/               # React components (Kanban, modals, chat)
│   │   ├── api/client.ts             # API client
│   │   ├── store/                    # Zustand stores (story + pipeline)
│   │   └── hooks/useWebSocket.ts     # WebSocket hook
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
| `GET /api/agents/{id}` | Get agent card (A2A discovery) |
| `GET /api/chat` | Get A2A chat messages |
| `POST /api/chat/send` | Send message to agent via A2A |

### WebSocket Events

| Event | Description |
|-------|-------------|
| `story:created` | New story added |
| `story:updated` | Story status/content changed |
| `task:created` | New task added |
| `task:updated` | Task status/content changed |
| `agent:status_changed` | Agent started/stopped work |
| `agent:chat` | A2A message between agents |
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

80 tests covering API endpoints, A2A protocol, agent workflows, multi-board operations, and database models.

## License

MIT
