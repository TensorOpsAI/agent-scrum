"""
Agent Management API - CRUD endpoints for dynamic agents.

This module provides endpoints for creating, reading, updating, and deleting
dynamically created agents, as well as listing available templates and tools.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.db.models import DynamicAgent, CustomTool
from app.agents.templates import list_templates, get_template
from app.agents.tools.registry import (
    list_builtin_tools,
    list_builtin_tools_by_category,
    get_builtin_categories,
    get_builtin_tool,
    DEFAULT_CATEGORIES,
)
from app.config import get_settings

settings = get_settings()


router = APIRouter(prefix="/api/agent-management", tags=["agent-management"])


# Request/Response Models
class SkillConfig(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str] = []
    examples: list[str] = []


class CreateAgentRequest(BaseModel):
    id: str  # Unique agent ID (e.g., "security_analyst_1")
    name: str
    description: Optional[str] = None
    template: Optional[str] = None  # Optional template to use
    tools: list[str] = []  # Tool IDs to include
    skills: list[SkillConfig] = []  # Custom skills
    capabilities: dict = {}


class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tools: Optional[list[str]] = None
    skills: Optional[list[SkillConfig]] = None
    capabilities: Optional[dict] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    template: Optional[str]
    tools: list[str]
    skills: list[dict]
    capabilities: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    default_tools: list[str]
    skills: list[dict]


class ToolResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    capabilities: list[str]
    is_builtin: bool = True


class CreateToolRequest(BaseModel):
    id: str  # Unique tool ID (e.g., "my_custom_tool")
    name: str
    description: Optional[str] = None
    category: str
    capabilities: list[str] = []
    config: dict = {}


class UpdateToolRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    capabilities: Optional[list[str]] = None
    config: Optional[dict] = None


# Template Endpoints
@router.get("/templates", response_model=list[TemplateResponse])
async def get_templates():
    """List all available agent templates."""
    templates = list_templates()
    return [
        TemplateResponse(
            id=t["id"],
            name=t["name"],
            description=t["description"],
            default_tools=t["default_tools"],
            skills=t["skills"],
        )
        for t in templates
    ]


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template_by_id(template_id: str):
    """Get a specific template by ID."""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return TemplateResponse(
        id=template_id,
        name=template["name"],
        description=template["description"],
        default_tools=template["default_tools"],
        skills=template["skills"],
    )


# Tool Endpoints
@router.get("/tools", response_model=list[ToolResponse])
async def get_tools(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all available tools (built-in + custom), optionally filtered by category."""
    # Get built-in tools
    if category:
        builtin = list_builtin_tools_by_category(category)
    else:
        builtin = list_builtin_tools()

    # Get custom tools from database
    query = select(CustomTool)
    if category:
        query = query.where(CustomTool.category == category)
    result = await db.execute(query)
    custom_tools = result.scalars().all()

    # Combine results
    all_tools = [
        ToolResponse(
            id=t["id"],
            name=t["name"],
            description=t["description"],
            category=t["category"],
            capabilities=t["capabilities"],
            is_builtin=True,
        )
        for t in builtin
    ]
    all_tools.extend([
        ToolResponse(
            id=t.id,
            name=t.name,
            description=t.description or "",
            category=t.category,
            capabilities=t.capabilities or [],
            is_builtin=False,
        )
        for t in custom_tools
    ])

    return all_tools


@router.get("/tools/categories", response_model=list[str])
async def get_tool_categories(db: AsyncSession = Depends(get_db)):
    """List all tool categories (built-in + custom)."""
    categories = set(get_builtin_categories())

    # Add categories from custom tools
    result = await db.execute(select(CustomTool.category).distinct())
    custom_categories = result.scalars().all()
    categories.update(custom_categories)

    return sorted(list(categories))


@router.get("/tools/{tool_id}", response_model=ToolResponse)
async def get_tool_by_id(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific tool by ID (built-in or custom)."""
    # Check built-in first
    builtin = get_builtin_tool(tool_id)
    if builtin:
        return ToolResponse(
            id=tool_id,
            name=builtin["name"],
            description=builtin["description"],
            category=builtin["category"],
            capabilities=builtin["capabilities"],
            is_builtin=True,
        )

    # Check custom tools
    result = await db.execute(select(CustomTool).where(CustomTool.id == tool_id))
    custom = result.scalar_one_or_none()
    if custom:
        return ToolResponse(
            id=custom.id,
            name=custom.name,
            description=custom.description or "",
            category=custom.category,
            capabilities=custom.capabilities or [],
            is_builtin=False,
        )

    raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")


@router.post("/tools", response_model=ToolResponse)
async def create_custom_tool(
    request: CreateToolRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom tool."""
    # Check if ID conflicts with built-in
    if get_builtin_tool(request.id):
        raise HTTPException(
            status_code=400,
            detail=f"Tool ID '{request.id}' conflicts with a built-in tool",
        )

    # Check if custom tool already exists
    existing = await db.execute(
        select(CustomTool).where(CustomTool.id == request.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Tool with ID '{request.id}' already exists",
        )

    tool = CustomTool(
        id=request.id,
        name=request.name,
        description=request.description,
        category=request.category,
        capabilities=request.capabilities,
        config=request.config,
        is_builtin=False,
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool)

    return ToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description or "",
        category=tool.category,
        capabilities=tool.capabilities or [],
        is_builtin=False,
    )


@router.put("/tools/{tool_id}", response_model=ToolResponse)
async def update_custom_tool(
    tool_id: str,
    request: UpdateToolRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a custom tool. Built-in tools cannot be modified."""
    # Check if trying to modify built-in
    if get_builtin_tool(tool_id):
        raise HTTPException(
            status_code=400,
            detail="Cannot modify built-in tools",
        )

    result = await db.execute(select(CustomTool).where(CustomTool.id == tool_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Custom tool not found: {tool_id}")

    # Update fields
    if request.name is not None:
        tool.name = request.name
    if request.description is not None:
        tool.description = request.description
    if request.category is not None:
        tool.category = request.category
    if request.capabilities is not None:
        tool.capabilities = request.capabilities
    if request.config is not None:
        tool.config = request.config

    await db.commit()
    await db.refresh(tool)

    return ToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description or "",
        category=tool.category,
        capabilities=tool.capabilities or [],
        is_builtin=False,
    )


@router.delete("/tools/{tool_id}")
async def delete_custom_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom tool. Built-in tools cannot be deleted."""
    # Check if trying to delete built-in
    if get_builtin_tool(tool_id):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete built-in tools",
        )

    result = await db.execute(select(CustomTool).where(CustomTool.id == tool_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Custom tool not found: {tool_id}")

    await db.delete(tool)
    await db.commit()

    return {"success": True, "message": f"Tool '{tool_id}' deleted"}


# Dynamic Agent CRUD Endpoints
@router.get("/agents", response_model=list[AgentResponse])
async def list_dynamic_agents(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all dynamic agents."""
    query = select(DynamicAgent)
    if is_active is not None:
        query = query.where(DynamicAgent.is_active == is_active)

    result = await db.execute(query.order_by(DynamicAgent.created_at.desc()))
    agents = result.scalars().all()

    return [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            template=agent.template,
            tools=agent.tools or [],
            skills=agent.skills or [],
            capabilities=agent.capabilities or {},
            is_active=agent.is_active,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )
        for agent in agents
    ]


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_dynamic_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific dynamic agent by ID."""
    result = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        template=agent.template,
        tools=agent.tools or [],
        skills=agent.skills or [],
        capabilities=agent.capabilities or {},
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.post("/agents", response_model=AgentResponse)
async def create_dynamic_agent(
    request: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new dynamic agent."""
    # Check if agent ID already exists
    existing = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == request.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Agent with ID '{request.id}' already exists",
        )

    # If using a template, apply defaults
    tools = request.tools
    skills = [s.model_dump() for s in request.skills]
    capabilities = request.capabilities
    description = request.description

    if request.template:
        template = get_template(request.template)
        if template:
            # Use template defaults if not provided
            if not tools:
                tools = template["default_tools"]
            if not skills:
                skills = template["skills"]
            if not description:
                description = template["description"]
            if not capabilities:
                capabilities = template.get("capabilities", {})

    agent = DynamicAgent(
        id=request.id,
        name=request.name,
        description=description,
        template=request.template,
        tools=tools,
        skills=skills,
        capabilities=capabilities,
        is_active=True,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        template=agent.template,
        tools=agent.tools or [],
        skills=agent.skills or [],
        capabilities=agent.capabilities or {},
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_dynamic_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing dynamic agent."""
    result = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    # Update fields
    if request.name is not None:
        agent.name = request.name
    if request.description is not None:
        agent.description = request.description
    if request.tools is not None:
        agent.tools = request.tools
    if request.skills is not None:
        agent.skills = [s.model_dump() for s in request.skills]
    if request.capabilities is not None:
        agent.capabilities = request.capabilities
    if request.is_active is not None:
        agent.is_active = request.is_active

    await db.commit()
    await db.refresh(agent)

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        template=agent.template,
        tools=agent.tools or [],
        skills=agent.skills or [],
        capabilities=agent.capabilities or {},
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.delete("/agents/{agent_id}")
async def delete_dynamic_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a dynamic agent."""
    result = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    await db.delete(agent)
    await db.commit()

    return {"success": True, "message": f"Agent '{agent_id}' deleted"}


@router.post("/agents/{agent_id}/activate")
async def toggle_agent_activation(
    agent_id: str,
    activate: bool = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate a dynamic agent."""
    result = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    agent.is_active = activate
    await db.commit()

    status = "activated" if activate else "deactivated"
    return {"success": True, "message": f"Agent '{agent_id}' {status}", "is_active": activate}


# A2A Discovery Endpoint
@router.get("/agents/{agent_id}/.well-known/agent.json")
async def get_agent_card(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the A2A agent card for a dynamic agent."""
    result = await db.execute(
        select(DynamicAgent).where(DynamicAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    if not agent.is_active:
        raise HTTPException(status_code=403, detail=f"Agent '{agent_id}' is not active")

    base_url = f"http://{settings.host}:{settings.port}"
    return {
        "name": agent.name,
        "description": agent.description or "",
        "url": f"{base_url}/api/agent-management/agents/{agent.id}",
        "capabilities": agent.capabilities or {},
        "skills": agent.skills or [],
    }
