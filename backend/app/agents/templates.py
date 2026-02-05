"""
Agent Templates - Pre-built templates for creating dynamic agents.

Templates define the default configuration for common agent types,
including their tools, skills, and descriptions.
"""
from typing import TypedDict


class SkillTemplate(TypedDict):
    id: str
    name: str
    description: str
    tags: list[str]
    examples: list[str]


class AgentTemplate(TypedDict):
    name: str
    description: str
    default_tools: list[str]
    skills: list[SkillTemplate]
    capabilities: dict[str, bool]


AGENT_TEMPLATES: dict[str, AgentTemplate] = {
    "security_analyst": {
        "name": "Security Analyst",
        "description": "Reviews code for security vulnerabilities and compliance issues",
        "default_tools": ["vulnerability_scanner", "secret_detector", "dependency_checker", "compliance_checker"],
        "skills": [
            {
                "id": "security_review",
                "name": "Security Review",
                "description": "Scan code for security vulnerabilities",
                "tags": ["security", "vulnerabilities", "scan"],
                "examples": ["Scan this PR for security issues", "Check for SQL injection vulnerabilities"],
            },
            {
                "id": "compliance_check",
                "name": "Compliance Check",
                "description": "Check security compliance against standards",
                "tags": ["compliance", "owasp", "standards"],
                "examples": ["Check OWASP compliance", "Verify security standards"],
            },
            {
                "id": "secret_scan",
                "name": "Secret Scan",
                "description": "Detect hardcoded secrets and credentials",
                "tags": ["secrets", "credentials", "scan"],
                "examples": ["Check for hardcoded API keys", "Scan for leaked credentials"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "documentation_writer": {
        "name": "Documentation Writer",
        "description": "Creates and maintains technical documentation",
        "default_tools": ["doc_generator", "api_documenter", "changelog_generator"],
        "skills": [
            {
                "id": "generate_docs",
                "name": "Generate Documentation",
                "description": "Generate documentation from code",
                "tags": ["docs", "documentation", "generate"],
                "examples": ["Generate docs for this module", "Create README"],
            },
            {
                "id": "document_api",
                "name": "Document API",
                "description": "Create API documentation with examples",
                "tags": ["api", "openapi", "swagger"],
                "examples": ["Document this API endpoint", "Generate OpenAPI spec"],
            },
            {
                "id": "write_changelog",
                "name": "Write Changelog",
                "description": "Generate changelog from changes",
                "tags": ["changelog", "release", "notes"],
                "examples": ["Generate changelog for this release", "Summarize changes"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "performance_engineer": {
        "name": "Performance Engineer",
        "description": "Analyzes and optimizes application performance",
        "default_tools": ["profiler", "memory_analyzer", "load_tester", "complexity_checker"],
        "skills": [
            {
                "id": "performance_analysis",
                "name": "Performance Analysis",
                "description": "Profile code and identify bottlenecks",
                "tags": ["performance", "profiling", "optimization"],
                "examples": ["Profile this function", "Find performance bottlenecks"],
            },
            {
                "id": "memory_check",
                "name": "Memory Check",
                "description": "Analyze memory usage and detect leaks",
                "tags": ["memory", "leaks", "analysis"],
                "examples": ["Check for memory leaks", "Analyze memory usage"],
            },
            {
                "id": "load_test",
                "name": "Load Test",
                "description": "Run load tests and report metrics",
                "tags": ["load", "stress", "testing"],
                "examples": ["Run load test", "Test under high concurrency"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "code_quality_analyst": {
        "name": "Code Quality Analyst",
        "description": "Ensures code quality through static analysis and best practices",
        "default_tools": ["static_analyzer", "complexity_checker", "linter", "code_formatter"],
        "skills": [
            {
                "id": "code_analysis",
                "name": "Code Analysis",
                "description": "Perform static code analysis",
                "tags": ["analysis", "static", "quality"],
                "examples": ["Analyze code quality", "Find code smells"],
            },
            {
                "id": "complexity_review",
                "name": "Complexity Review",
                "description": "Review and report on code complexity",
                "tags": ["complexity", "cyclomatic", "cognitive"],
                "examples": ["Measure code complexity", "Find complex functions"],
            },
            {
                "id": "style_check",
                "name": "Style Check",
                "description": "Check code style and formatting",
                "tags": ["style", "formatting", "lint"],
                "examples": ["Check code style", "Find style violations"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "test_engineer": {
        "name": "Test Engineer",
        "description": "Generates tests and ensures code coverage",
        "default_tools": ["test_generator", "coverage_analyzer", "mutation_tester"],
        "skills": [
            {
                "id": "generate_tests",
                "name": "Generate Tests",
                "description": "Generate unit tests for code",
                "tags": ["tests", "unit", "generate"],
                "examples": ["Generate tests for this class", "Create test cases"],
            },
            {
                "id": "coverage_analysis",
                "name": "Coverage Analysis",
                "description": "Analyze test coverage",
                "tags": ["coverage", "analysis", "metrics"],
                "examples": ["Check test coverage", "Find untested code"],
            },
            {
                "id": "test_quality",
                "name": "Test Quality",
                "description": "Assess test quality through mutation testing",
                "tags": ["mutation", "quality", "testing"],
                "examples": ["Run mutation testing", "Assess test effectiveness"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "devops_engineer": {
        "name": "DevOps Engineer",
        "description": "Manages CI/CD and infrastructure configurations",
        "default_tools": ["dockerfile_analyzer", "ci_config_checker"],
        "skills": [
            {
                "id": "dockerfile_review",
                "name": "Dockerfile Review",
                "description": "Review Dockerfile for best practices",
                "tags": ["docker", "containers", "review"],
                "examples": ["Review Dockerfile", "Check Docker security"],
            },
            {
                "id": "ci_validation",
                "name": "CI Validation",
                "description": "Validate CI/CD configurations",
                "tags": ["ci", "cd", "validation"],
                "examples": ["Validate CI config", "Check pipeline syntax"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "scrum_master": {
        "name": "Scrum Master",
        "description": "Coordinates the team workflow, unblocks stuck tasks, and ensures smooth handoffs between agents. Monitors the board and chat for issues that need intervention.",
        "default_tools": ["static_analyzer"],  # Minimal tools - mainly coordinates
        "skills": [
            {
                "id": "check_blocked_tasks",
                "name": "Check Blocked Tasks",
                "description": "Scan the board for tasks that are stuck or waiting for action. Identify tasks where feedback was given but no follow-up occurred.",
                "tags": ["workflow", "blocked", "stuck", "monitor"],
                "examples": [
                    "Check for stuck tasks",
                    "Find tasks waiting for developer response",
                    "Which tasks have unresolved feedback?",
                ],
            },
            {
                "id": "reassign_task",
                "name": "Reassign Task",
                "description": "Move a task back to a previous stage when issues are found. For example, move a task from QA back to Development when bugs are reported.",
                "tags": ["reassign", "workflow", "transition", "unblock"],
                "examples": [
                    "Move TASK-25 back to development",
                    "Reassign task to developer for fixes",
                    "Send task back for rework",
                ],
            },
            {
                "id": "follow_up",
                "name": "Follow Up",
                "description": "Send reminders to agents who haven't responded to feedback or picked up assigned work. Nudge the team to keep work flowing.",
                "tags": ["reminder", "follow-up", "nudge", "communication"],
                "examples": [
                    "Remind developer about QA feedback on TASK-13",
                    "Follow up on pending code review",
                    "Nudge tech lead about task review",
                ],
            },
            {
                "id": "daily_standup",
                "name": "Daily Standup Summary",
                "description": "Summarize the current state of the board: what's in progress, what's blocked, what was completed. Highlight any items needing attention.",
                "tags": ["standup", "summary", "status", "report"],
                "examples": [
                    "Give me a standup summary",
                    "What's the current board status?",
                    "Summarize today's progress",
                ],
            },
            {
                "id": "resolve_conflict",
                "name": "Resolve Conflict",
                "description": "Mediate when there are disagreements between agents or unclear ownership of tasks. Clarify responsibilities and next steps.",
                "tags": ["conflict", "mediation", "ownership", "clarify"],
                "examples": [
                    "Clarify who should fix this bug",
                    "Resolve the dispute about task scope",
                    "Who owns this task now?",
                ],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": True,  # Can send proactive notifications
            "state_transition_history": True,
        },
    },
}


def get_template(template_id: str) -> AgentTemplate | None:
    """Get an agent template by ID."""
    return AGENT_TEMPLATES.get(template_id)


def list_templates() -> list[dict]:
    """List all available templates."""
    return [
        {"id": template_id, **template}
        for template_id, template in AGENT_TEMPLATES.items()
    ]
