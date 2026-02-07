"""
Pipeline Templates - Preset column configurations for different workflows.

Each template defines the columns (statuses) for the Kanban board,
whether agent automation is enabled, the noun used for items,
and the domain-specific agents that work on items.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# Preset Templates
# ============================================================================

PIPELINE_TEMPLATES = [
    {
        "template_id": "software_dev",
        "name": "Software Development",
        "columns": [
            {"key": "backlog", "label": "Backlog", "color": "bg-gray-600", "position": 0},
            {"key": "ready_for_breakdown", "label": "Ready for Breakdown", "color": "bg-blue-600", "position": 1},
            {"key": "in_breakdown", "label": "In Breakdown", "color": "bg-blue-500", "position": 2},
            {"key": "tasks_in_review", "label": "Tasks in Review", "color": "bg-purple-600", "position": 3},
            {"key": "in_development", "label": "In Development", "color": "bg-yellow-600", "position": 4},
            {"key": "in_qa", "label": "In QA", "color": "bg-pink-600", "position": 5},
            {"key": "done", "label": "Done", "color": "bg-green-600", "position": 6},
        ],
        "agent_automation": True,
        "item_noun": "Story",
        "has_tasks": True,
        "sub_item_noun": "Task",
        "input_noun": "PRD",
        "epic_noun": "Epic",
        "input_placeholder": "Paste your Product Requirements Document here...\n\nExample:\n# Feature: User Authentication\n## Overview\nImplement a secure user authentication system...\n\n## Requirements\n- Users should be able to sign up with email\n- Users should be able to log in\n- Sessions should be secure...",
        "sub_item_statuses": ["draft", "pending_review", "ready_for_development", "in_progress", "code_review", "ready_for_qa", "qa_in_progress", "done"],
        "item_source": "internal",
        "intake_agent": "product_owner",
        "manager_role": "scrum_master",
        "agents": [
            {"role": "product_owner", "name": "Product Owner", "description": "Parses PRDs and creates user stories with acceptance criteria", "tools": ["prd_parser", "story_generator"]},
            {"role": "developer", "name": "Developer", "description": "Breaks down stories into tasks and creates implementation notes", "tools": ["story_breakdown", "code_generator"]},
            {"role": "tech_lead", "name": "Tech Lead", "description": "Reviews task breakdowns and provides technical guidance", "tools": ["task_reviewer", "architecture_analyzer"]},
            {"role": "code_reviewer", "name": "Code Reviewer", "description": "Reviews implementation notes and provides feedback", "tools": ["code_analyzer", "security_scanner"]},
            {"role": "qa", "name": "QA", "description": "Creates test scenarios and runs simulated tests", "tools": ["test_generator", "test_runner"]},
            {"role": "scrum_master", "name": "Scrum Master", "description": "Coordinates the team workflow and assigns work to agents", "tools": ["workflow_monitor", "blocker_resolver"], "is_active": True},
        ],
    },
    {
        "template_id": "talent_acquisition",
        "name": "Talent Acquisition",
        "columns": [
            {"key": "sourced", "label": "Sourced", "color": "bg-gray-600", "position": 0},
            {"key": "applied", "label": "Applied", "color": "bg-blue-600", "position": 1},
            {"key": "phone_screen", "label": "Phone Screen", "color": "bg-indigo-600", "position": 2},
            {"key": "interview", "label": "Interview", "color": "bg-purple-600", "position": 3},
            {"key": "offer", "label": "Offer", "color": "bg-yellow-600", "position": 4},
            {"key": "hired", "label": "Hired", "color": "bg-green-600", "position": 5},
        ],
        "agent_automation": True,
        "item_noun": "Candidate",
        "has_tasks": True,
        "sub_item_noun": "Interview Step",
        "input_noun": "Job Requisition",
        "epic_noun": "Position",
        "input_placeholder": "Paste the job requisition here...\n\nExample:\n# Position: Senior Software Engineer\n## Department\nEngineering\n\n## Requirements\n- 5+ years experience in backend development\n- Strong Python and SQL skills\n- Experience with cloud platforms",
        "sub_item_statuses": ["pending", "scheduled", "in_progress", "review", "done"],
        "item_source": "external",
        "intake_agent": "sourcing_specialist",
        "manager_role": "hiring_manager",
        "agents": [
            {"role": "sourcing_specialist", "name": "Sourcing Specialist", "description": "Finds candidates via job boards and LinkedIn", "tools": ["resume_parser", "candidate_scorer"]},
            {"role": "recruiter", "name": "Recruiter", "description": "Manages pipeline, screens candidates, conducts phone screens", "tools": ["resume_parser", "interview_scheduler"]},
            {"role": "hiring_manager", "name": "Hiring Manager", "description": "Reviews candidates and makes hiring decisions", "tools": ["candidate_scorer"]},
            {"role": "interview_coordinator", "name": "Interview Coordinator", "description": "Schedules interviews and manages logistics", "tools": ["interview_scheduler"]},
            {"role": "hr_coordinator", "name": "HR Coordinator", "description": "Prepares offers and handles onboarding", "tools": ["background_checker"]},
        ],
    },
    {
        "template_id": "sales",
        "name": "Sales",
        "columns": [
            {"key": "lead", "label": "Lead", "color": "bg-gray-600", "position": 0},
            {"key": "qualified", "label": "Qualified", "color": "bg-blue-600", "position": 1},
            {"key": "proposal", "label": "Proposal", "color": "bg-indigo-600", "position": 2},
            {"key": "negotiation", "label": "Negotiation", "color": "bg-yellow-600", "position": 3},
            {"key": "closed_won", "label": "Closed Won", "color": "bg-green-600", "position": 4},
            {"key": "closed_lost", "label": "Closed Lost", "color": "bg-red-600", "position": 5},
        ],
        "agent_automation": True,
        "item_noun": "Deal",
        "has_tasks": True,
        "sub_item_noun": "Action Item",
        "input_noun": "Lead List",
        "epic_noun": "Account",
        "input_placeholder": "Paste the lead list or prospect information here...\n\nExample:\n# Account: Acme Corp\n## Contact\nJohn Smith, VP Engineering\n\n## Opportunity\n- Looking for enterprise solution\n- Budget: $50K-100K\n- Timeline: Q2 2025",
        "sub_item_statuses": ["pending", "in_progress", "review", "done"],
        "item_source": "external",
        "intake_agent": "lead_generator",
        "manager_role": "sales_manager",
        "agents": [
            {"role": "lead_generator", "name": "Lead Generator", "description": "Sources and qualifies inbound/outbound leads", "tools": ["lead_scorer", "crm_connector"]},
            {"role": "account_executive", "name": "Account Executive", "description": "Manages deals, runs demos, creates proposals", "tools": ["proposal_generator", "crm_connector"]},
            {"role": "sales_manager", "name": "Sales Manager", "description": "Reviews deals and approves discounts", "tools": ["crm_connector"]},
            {"role": "solutions_engineer", "name": "Solutions Engineer", "description": "Technical pre-sales, builds POCs", "tools": ["proposal_generator"]},
            {"role": "contract_specialist", "name": "Contract Specialist", "description": "Handles negotiations and contracts", "tools": ["contract_builder"]},
        ],
    },
    {
        "template_id": "ciso",
        "name": "CISO",
        "columns": [
            {"key": "identified", "label": "Identified", "color": "bg-red-600", "position": 0},
            {"key": "assessing", "label": "Assessing", "color": "bg-orange-600", "position": 1},
            {"key": "mitigating", "label": "Mitigating", "color": "bg-yellow-600", "position": 2},
            {"key": "monitoring", "label": "Monitoring", "color": "bg-blue-600", "position": 3},
            {"key": "resolved", "label": "Resolved", "color": "bg-green-600", "position": 4},
        ],
        "agent_automation": True,
        "item_noun": "Risk",
        "has_tasks": True,
        "sub_item_noun": "Mitigation Step",
        "input_noun": "Incident Report",
        "epic_noun": "Threat Category",
        "input_placeholder": "Paste the incident report or threat intelligence here...\n\nExample:\n# Incident: SQL Injection on Login API\n## Severity\nHigh (CVSS 7.8)\n\n## Details\n- Affected endpoint: /api/auth/login\n- Attack vector: user input in email field\n- Discovered via automated scanning",
        "sub_item_statuses": ["identified", "in_progress", "review", "verified", "done"],
        "item_source": "external",
        "intake_agent": "threat_analyst",
        "manager_role": "risk_manager",
        "agents": [
            {"role": "threat_analyst", "name": "Threat Analyst", "description": "Identifies and classifies security risks", "tools": ["threat_detector", "compliance_auditor"]},
            {"role": "security_engineer", "name": "Security Engineer", "description": "Implements mitigations and patches", "tools": ["patch_manager", "threat_detector"]},
            {"role": "compliance_officer", "name": "Compliance Officer", "description": "Ensures regulatory compliance", "tools": ["compliance_auditor"]},
            {"role": "incident_responder", "name": "Incident Responder", "description": "Handles active security incidents", "tools": ["incident_tracker", "threat_detector"]},
            {"role": "risk_manager", "name": "Risk Manager", "description": "Oversees the risk portfolio", "tools": ["incident_tracker"]},
        ],
    },
]


# ============================================================================
# Workflow Rules per Template
# ============================================================================
# Maps column keys to (agent_role, action, next_status) for the swarm to dispatch.

TEMPLATE_WORKFLOWS = {
    "software_dev": {
        "story_handlers": {
            "ready_for_breakdown": ("developer", "breakdown", "in_breakdown"),
            "tasks_in_review": ("tech_lead", "review_tasks", "in_development"),
        },
        "task_handlers": {
            "ready_for_development": ("developer", "implementation", "code_review"),
            "code_review": ("code_reviewer", "code_review", "ready_for_qa"),
            "ready_for_qa": ("qa", "qa_scenarios", "qa_in_progress"),
            "qa_in_progress": ("qa", "qa_run", "done"),
        },
    },
    "talent_acquisition": {
        "story_handlers": {
            "applied": ("recruiter", "screen_resume", "phone_screen"),
            "phone_screen": ("recruiter", "phone_screen", "interview"),
            "interview": ("interview_coordinator", "schedule_interview", "offer"),
            "offer": ("hr_coordinator", "prepare_offer", "hired"),
        },
        "task_handlers": {
            "pending": ("hiring_manager", "evaluate", "scheduled"),
            "scheduled": ("interview_coordinator", "conduct", "in_progress"),
            "in_progress": ("hiring_manager", "review_feedback", "review"),
            "review": ("hr_coordinator", "verify", "done"),
        },
    },
    "sales": {
        "story_handlers": {
            "qualified": ("account_executive", "qualify_lead", "proposal"),
            "proposal": ("account_executive", "create_proposal", "negotiation"),
            "negotiation": ("contract_specialist", "negotiate", "closed_won"),
        },
        "task_handlers": {
            "pending": ("solutions_engineer", "build_poc", "in_progress"),
            "in_progress": ("account_executive", "demo", "review"),
            "review": ("sales_manager", "review_deal", "done"),
        },
    },
    "ciso": {
        "story_handlers": {
            "assessing": ("threat_analyst", "assess_threat", "mitigating"),
            "mitigating": ("security_engineer", "mitigate", "monitoring"),
            "monitoring": ("compliance_officer", "audit", "resolved"),
        },
        "task_handlers": {
            "identified": ("security_engineer", "implement_control", "in_progress"),
            "in_progress": ("security_engineer", "deploy_fix", "review"),
            "review": ("compliance_officer", "compliance_review", "verified"),
            "verified": ("incident_responder", "verify_mitigation", "done"),
        },
    },
}


def get_template_by_id(template_id: str) -> Optional[dict]:
    """Get a preset template by its ID."""
    for t in PIPELINE_TEMPLATES:
        if t["template_id"] == template_id:
            return t
    return None


def get_template_manager_role(template_id: str) -> Optional[str]:
    """Get the manager role for a template (e.g., 'scrum_master' for software_dev)."""
    template = get_template_by_id(template_id)
    return template.get("manager_role") if template else None


async def get_board(board_id: int, db: AsyncSession) -> Optional[dict]:
    """Get a board (PipelineConfig) by ID and return as dict."""
    from app.db.models import PipelineConfig

    result = await db.execute(
        select(PipelineConfig).where(PipelineConfig.id == board_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        return None

    return {
        "id": config.id,
        "template_id": config.template_id,
        "name": config.name,
        "columns": config.columns,
        "agent_automation": config.agent_automation,
        "item_noun": config.item_noun,
        "has_tasks": config.has_tasks,
        "sub_item_noun": config.sub_item_noun or "Task",
        "input_noun": config.input_noun or "PRD",
        "epic_noun": config.epic_noun or "Epic",
        "input_placeholder": config.input_placeholder,
        "sub_item_statuses": config.sub_item_statuses,
        "item_source": config.item_source or "internal",
    }


def get_valid_statuses(pipeline: dict) -> list[str]:
    """Get the list of valid status keys for a pipeline."""
    return [col["key"] for col in pipeline["columns"]]


def get_first_status(pipeline: dict) -> str:
    """Get the first column key (default status) for a pipeline."""
    return pipeline["columns"][0]["key"]
