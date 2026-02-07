"""
Tool Registry - Available tools that dynamic agents can use.

This module defines the "tool basket" - a collection of tools that can be
assigned to dynamically created agents. Supports both built-in and custom tools.
"""
from typing import TypedDict


class ToolDefinition(TypedDict):
    name: str
    description: str
    category: str
    capabilities: list[str]
    is_builtin: bool


# Built-in tools for dynamic agents
BUILTIN_TOOLS: dict[str, ToolDefinition] = {
    # Security tools
    "vulnerability_scanner": {
        "name": "Vulnerability Scanner",
        "description": "Scans code for common security vulnerabilities (SQL injection, XSS, etc.)",
        "category": "security",
        "capabilities": ["scan_code", "report_vulnerabilities", "suggest_fixes"],
        "is_builtin": True,
    },
    "dependency_checker": {
        "name": "Dependency Checker",
        "description": "Checks dependencies for known security issues and outdated packages",
        "category": "security",
        "capabilities": ["check_dependencies", "report_cves", "suggest_upgrades"],
        "is_builtin": True,
    },
    "secret_detector": {
        "name": "Secret Detector",
        "description": "Detects hardcoded secrets, API keys, and credentials in code",
        "category": "security",
        "capabilities": ["scan_secrets", "report_leaks", "suggest_env_vars"],
        "is_builtin": True,
    },
    "compliance_checker": {
        "name": "Compliance Checker",
        "description": "Checks code for compliance with security standards (OWASP, etc.)",
        "category": "security",
        "capabilities": ["check_compliance", "report_issues", "provide_guidance"],
        "is_builtin": True,
    },

    # Code analysis tools
    "static_analyzer": {
        "name": "Static Analyzer",
        "description": "Performs static code analysis for bugs, code smells, and anti-patterns",
        "category": "code",
        "capabilities": ["analyze_code", "report_issues", "suggest_improvements"],
        "is_builtin": True,
    },
    "complexity_checker": {
        "name": "Complexity Checker",
        "description": "Measures and reports on code complexity (cyclomatic, cognitive)",
        "category": "code",
        "capabilities": ["measure_complexity", "identify_hotspots", "suggest_refactoring"],
        "is_builtin": True,
    },
    "code_formatter": {
        "name": "Code Formatter",
        "description": "Formats code according to style guidelines",
        "category": "code",
        "capabilities": ["format_code", "check_style", "auto_fix"],
        "is_builtin": True,
    },
    "linter": {
        "name": "Linter",
        "description": "Lints code for style issues and potential errors",
        "category": "code",
        "capabilities": ["lint_code", "report_warnings", "auto_fix"],
        "is_builtin": True,
    },

    # Testing tools
    "test_generator": {
        "name": "Test Generator",
        "description": "Generates unit test cases for code",
        "category": "testing",
        "capabilities": ["generate_tests", "suggest_test_cases", "create_mocks"],
        "is_builtin": True,
    },
    "coverage_analyzer": {
        "name": "Coverage Analyzer",
        "description": "Analyzes test coverage and identifies untested code",
        "category": "testing",
        "capabilities": ["measure_coverage", "identify_gaps", "report_metrics"],
        "is_builtin": True,
    },
    "mutation_tester": {
        "name": "Mutation Tester",
        "description": "Tests test quality by introducing mutations",
        "category": "testing",
        "capabilities": ["run_mutations", "report_survival", "suggest_improvements"],
        "is_builtin": True,
    },

    # Documentation tools
    "doc_generator": {
        "name": "Documentation Generator",
        "description": "Generates documentation from code comments and structure",
        "category": "docs",
        "capabilities": ["generate_docs", "extract_comments", "create_readme"],
        "is_builtin": True,
    },
    "api_documenter": {
        "name": "API Documenter",
        "description": "Documents API endpoints with OpenAPI/Swagger specs",
        "category": "docs",
        "capabilities": ["document_api", "generate_openapi", "create_examples"],
        "is_builtin": True,
    },
    "changelog_generator": {
        "name": "Changelog Generator",
        "description": "Generates changelog entries from commits and PRs",
        "category": "docs",
        "capabilities": ["generate_changelog", "categorize_changes", "format_entries"],
        "is_builtin": True,
    },

    # Performance tools
    "profiler": {
        "name": "Performance Profiler",
        "description": "Profiles code for performance bottlenecks",
        "category": "performance",
        "capabilities": ["profile_code", "identify_bottlenecks", "suggest_optimizations"],
        "is_builtin": True,
    },
    "memory_analyzer": {
        "name": "Memory Analyzer",
        "description": "Analyzes memory usage and identifies leaks",
        "category": "performance",
        "capabilities": ["analyze_memory", "detect_leaks", "report_usage"],
        "is_builtin": True,
    },
    "load_tester": {
        "name": "Load Tester",
        "description": "Tests application performance under load",
        "category": "performance",
        "capabilities": ["run_load_tests", "report_metrics", "identify_limits"],
        "is_builtin": True,
    },

    # DevOps tools
    "dockerfile_analyzer": {
        "name": "Dockerfile Analyzer",
        "description": "Analyzes Dockerfiles for best practices and security",
        "category": "devops",
        "capabilities": ["analyze_dockerfile", "suggest_improvements", "check_security"],
        "is_builtin": True,
    },
    "ci_config_checker": {
        "name": "CI Config Checker",
        "description": "Validates CI/CD configuration files",
        "category": "devops",
        "capabilities": ["validate_config", "suggest_improvements", "check_syntax"],
        "is_builtin": True,
    },

    # HR / Talent Acquisition tools
    "resume_parser": {
        "name": "Resume Parser",
        "description": "Parses and extracts structured data from candidate resumes",
        "category": "hr",
        "capabilities": ["parse_resume", "extract_skills", "score_experience"],
        "is_builtin": True,
    },
    "interview_scheduler": {
        "name": "Interview Scheduler",
        "description": "Schedules interviews and manages calendar logistics",
        "category": "hr",
        "capabilities": ["schedule_interview", "send_invites", "manage_availability"],
        "is_builtin": True,
    },
    "candidate_scorer": {
        "name": "Candidate Scorer",
        "description": "Scores candidates against job requirements and team fit",
        "category": "hr",
        "capabilities": ["score_candidate", "rank_applicants", "generate_report"],
        "is_builtin": True,
    },
    "background_checker": {
        "name": "Background Checker",
        "description": "Runs background and reference checks on candidates",
        "category": "hr",
        "capabilities": ["verify_employment", "check_references", "generate_report"],
        "is_builtin": True,
    },

    # Sales tools
    "lead_scorer": {
        "name": "Lead Scorer",
        "description": "Scores and qualifies sales leads based on fit and intent signals",
        "category": "sales",
        "capabilities": ["score_lead", "qualify_lead", "prioritize_pipeline"],
        "is_builtin": True,
    },
    "proposal_generator": {
        "name": "Proposal Generator",
        "description": "Generates customized sales proposals and SOWs",
        "category": "sales",
        "capabilities": ["generate_proposal", "customize_template", "calculate_pricing"],
        "is_builtin": True,
    },
    "crm_connector": {
        "name": "CRM Connector",
        "description": "Syncs deal data with CRM systems like Salesforce or HubSpot",
        "category": "sales",
        "capabilities": ["sync_deals", "update_pipeline", "log_activities"],
        "is_builtin": True,
    },
    "contract_builder": {
        "name": "Contract Builder",
        "description": "Builds and manages sales contracts and agreements",
        "category": "sales",
        "capabilities": ["draft_contract", "track_signatures", "manage_terms"],
        "is_builtin": True,
    },

    # Security / CISO tools
    "threat_detector": {
        "name": "Threat Detector",
        "description": "Detects and classifies security threats and vulnerabilities",
        "category": "infosec",
        "capabilities": ["detect_threats", "classify_risk", "alert_team"],
        "is_builtin": True,
    },
    "patch_manager": {
        "name": "Patch Manager",
        "description": "Manages security patch deployment and tracking",
        "category": "infosec",
        "capabilities": ["identify_patches", "schedule_deployment", "verify_installation"],
        "is_builtin": True,
    },
    "compliance_auditor": {
        "name": "Compliance Auditor",
        "description": "Audits systems for regulatory compliance (SOC2, NIST, etc.)",
        "category": "infosec",
        "capabilities": ["audit_controls", "generate_evidence", "track_findings"],
        "is_builtin": True,
    },
    "incident_tracker": {
        "name": "Incident Tracker",
        "description": "Tracks and manages security incidents through resolution",
        "category": "infosec",
        "capabilities": ["log_incident", "track_response", "generate_postmortem"],
        "is_builtin": True,
    },
}

# Default categories (custom tools can add more)
DEFAULT_CATEGORIES = ["security", "code", "testing", "docs", "performance", "devops", "hr", "sales", "infosec"]


def get_builtin_tool(tool_id: str) -> ToolDefinition | None:
    """Get a built-in tool definition by ID."""
    return BUILTIN_TOOLS.get(tool_id)


def list_builtin_tools() -> list[dict]:
    """List all built-in tools."""
    return [
        {"id": tool_id, **tool_def}
        for tool_id, tool_def in BUILTIN_TOOLS.items()
    ]


def list_builtin_tools_by_category(category: str) -> list[dict]:
    """List built-in tools filtered by category."""
    return [
        {"id": tool_id, **tool_def}
        for tool_id, tool_def in BUILTIN_TOOLS.items()
        if tool_def["category"] == category
    ]


def get_builtin_categories() -> list[str]:
    """Get list of built-in tool categories."""
    return DEFAULT_CATEGORIES.copy()


# Legacy aliases for backwards compatibility
AVAILABLE_TOOLS = BUILTIN_TOOLS
get_tool = get_builtin_tool
list_tools = list_builtin_tools
list_tools_by_category = list_builtin_tools_by_category
get_categories = get_builtin_categories
