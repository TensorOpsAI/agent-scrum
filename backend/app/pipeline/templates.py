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
        "agents": [
            {"role": "product_owner", "name": "Product Owner", "description": "Parses PRDs and creates user stories with acceptance criteria", "tools": ["prd_parser", "story_generator"]},
            {"role": "developer", "name": "Developer", "description": "Breaks down stories into tasks and creates implementation notes", "tools": ["story_breakdown", "code_generator"]},
            {"role": "tech_lead", "name": "Tech Lead", "description": "Reviews task breakdowns and provides technical guidance", "tools": ["task_reviewer", "architecture_analyzer"]},
            {"role": "code_reviewer", "name": "Code Reviewer", "description": "Reviews implementation notes and provides feedback", "tools": ["code_analyzer", "security_scanner"]},
            {"role": "qa", "name": "QA", "description": "Creates test scenarios and runs simulated tests", "tools": ["test_generator", "test_runner"]},
            {"role": "scrum_master", "name": "Scrum Master", "description": "Coordinates the team workflow and unblocks stuck tasks (optional)", "tools": ["workflow_monitor", "blocker_resolver"], "is_active": False},
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
# Maps column keys to (agent_role, action) for the swarm to dispatch.

TEMPLATE_WORKFLOWS = {
    "software_dev": {
        "story_handlers": {
            "ready_for_breakdown": ("developer", "breakdown"),
            "tasks_in_review": ("tech_lead", "review_tasks"),
        },
        "task_handlers": {
            "ready_for_development": ("developer", "implementation"),
            "code_review": ("code_reviewer", "code_review"),
            "ready_for_qa": ("qa", "qa_scenarios"),
            "qa_in_progress": ("qa", "qa_run"),
        },
    },
    "talent_acquisition": {
        "story_handlers": {
            "applied": ("recruiter", "screen_resume"),
            "phone_screen": ("recruiter", "phone_screen"),
            "interview": ("interview_coordinator", "schedule_interview"),
            "offer": ("hr_coordinator", "prepare_offer"),
        },
        "task_handlers": {
            "ready_for_development": ("hiring_manager", "evaluate"),
            "in_progress": ("interview_coordinator", "conduct"),
            "code_review": ("hiring_manager", "review_feedback"),
            "ready_for_qa": ("hr_coordinator", "verify"),
            "qa_in_progress": ("hr_coordinator", "finalize"),
        },
    },
    "sales": {
        "story_handlers": {
            "qualified": ("account_executive", "qualify_lead"),
            "proposal": ("account_executive", "create_proposal"),
            "negotiation": ("contract_specialist", "negotiate"),
        },
        "task_handlers": {
            "ready_for_development": ("solutions_engineer", "build_poc"),
            "in_progress": ("account_executive", "demo"),
            "code_review": ("sales_manager", "review_deal"),
            "ready_for_qa": ("contract_specialist", "draft_contract"),
            "qa_in_progress": ("contract_specialist", "finalize_contract"),
        },
    },
    "ciso": {
        "story_handlers": {
            "assessing": ("threat_analyst", "assess_threat"),
            "mitigating": ("security_engineer", "mitigate"),
            "monitoring": ("compliance_officer", "audit"),
        },
        "task_handlers": {
            "ready_for_development": ("security_engineer", "implement_control"),
            "in_progress": ("security_engineer", "deploy_fix"),
            "code_review": ("compliance_officer", "compliance_review"),
            "ready_for_qa": ("incident_responder", "verify_mitigation"),
            "qa_in_progress": ("risk_manager", "assess_residual"),
        },
    },
}


def get_template_by_id(template_id: str) -> Optional[dict]:
    """Get a preset template by its ID."""
    for t in PIPELINE_TEMPLATES:
        if t["template_id"] == template_id:
            return t
    return None


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
    }


def get_valid_statuses(pipeline: dict) -> list[str]:
    """Get the list of valid status keys for a pipeline."""
    return [col["key"] for col in pipeline["columns"]]


def get_first_status(pipeline: dict) -> str:
    """Get the first column key (default status) for a pipeline."""
    return pipeline["columns"][0]["key"]
