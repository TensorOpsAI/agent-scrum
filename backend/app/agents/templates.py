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

    "news_curator": {
        "name": "Curador de Noticias",
        "description": "Explora fuentes de noticias, temas de tendencia y feeds RSS para identificar elementos de interés para su cobertura. Selecciona historias con alto potencial de interés para el lector.",
        "default_tools": ["rss_reader", "trend_analyzer"],
        "skills": [
            {
                "id": "scan_sources",
                "name": "Scan News Sources",
                "description": "Monitor RSS feeds, news aggregators, and social media for breaking stories and trending topics",
                "tags": ["news", "rss", "trending", "sources"],
                "examples": ["Scan for breaking news", "What's trending today?", "Find stories about AI"],
            },
            {
                "id": "evaluate_newsworthiness",
                "name": "Evaluate Newsworthiness",
                "description": "Assess whether a topic has enough reader interest, timeliness, and impact to warrant coverage",
                "tags": ["evaluation", "editorial", "priority"],
                "examples": ["Is this story worth covering?", "Rate the newsworthiness of this topic"],
            },
            {
                "id": "create_brief",
                "name": "Create News Brief",
                "description": "Compile a structured news brief with key facts, sources, and suggested angles for journalists",
                "tags": ["brief", "assignment", "angles"],
                "examples": ["Create a brief for this story", "Summarize the key facts"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": True,
            "state_transition_history": True,
        },
    },

    "journalist": {
        "name": "Periodista",
        "description": "Redacta artículos a partir de las noticias seleccionadas, investigando, estructurando el contenido y produciendo piezas listas para publicar que cumplen con los estándares editoriales.",
        "default_tools": ["article_writer", "fact_checker"],
        "skills": [
            {
                "id": "write_article",
                "name": "Write Article",
                "description": "Draft a complete article with headline, lede, body, and conclusion from a news brief or topic",
                "tags": ["writing", "article", "draft"],
                "examples": ["Write an article about this topic", "Draft a piece on the latest developments"],
            },
            {
                "id": "research_topic",
                "name": "Research Topic",
                "description": "Gather background information, statistics, and expert opinions to support an article",
                "tags": ["research", "facts", "background"],
                "examples": ["Research background on this story", "Find supporting data for the article"],
            },
            {
                "id": "draft_section",
                "name": "Draft Section",
                "description": "Write a specific section of an article with supporting details and source attributions",
                "tags": ["section", "draft", "writing"],
                "examples": ["Write the introduction section", "Draft the analysis section"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "editor": {
        "name": "Editor",
        "description": "Revisa los artículos en cuanto a calidad, precisión, tono y cumplimiento de los estándares editoriales. Se asegura de que el contenido esté listo para publicar.",
        "default_tools": ["grammar_checker", "plagiarism_detector"],
        "skills": [
            {
                "id": "review_article",
                "name": "Review Article",
                "description": "Perform a comprehensive editorial review checking grammar, facts, tone, and structure",
                "tags": ["review", "editing", "quality"],
                "examples": ["Review this article for publication", "Edit the draft for quality"],
            },
            {
                "id": "fact_check",
                "name": "Fact Check",
                "description": "Verify all claims, statistics, and quotes in the article against reliable sources",
                "tags": ["facts", "verification", "accuracy"],
                "examples": ["Fact-check this article", "Verify the claims in paragraph 3"],
            },
            {
                "id": "style_review",
                "name": "Style Review",
                "description": "Ensure the article follows AP style, brand voice, and editorial guidelines",
                "tags": ["style", "guidelines", "tone"],
                "examples": ["Check style guide compliance", "Review tone consistency"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "creative_director": {
        "name": "Director Creativo",
        "description": "Selecciona o genera imágenes, miniaturas y elementos creativos para los artículos. Se asegura de que los recursos visuales encajen con el tono del contenido y las directrices de marca.",
        "default_tools": ["image_generator", "asset_library"],
        "skills": [
            {
                "id": "create_visuals",
                "name": "Create Visuals",
                "description": "Select or generate hero images, thumbnails, and infographics that complement article content",
                "tags": ["visuals", "images", "creative"],
                "examples": ["Create visuals for this article", "Generate a hero image"],
            },
            {
                "id": "brand_review",
                "name": "Brand Review",
                "description": "Ensure all visual assets meet brand guidelines for color, typography, and style",
                "tags": ["brand", "guidelines", "consistency"],
                "examples": ["Check brand compliance of images", "Review thumbnail against guidelines"],
            },
            {
                "id": "social_assets",
                "name": "Social Media Assets",
                "description": "Create optimized visual assets for social media promotion of articles",
                "tags": ["social", "promotion", "assets"],
                "examples": ["Create social media graphics", "Design shareable images"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "publisher_agent": {
        "name": "Publicador",
        "description": "Da formato y publica el contenido final en plataformas CMS, gestiona el calendario de publicación y optimiza para SEO.",
        "default_tools": ["cms_connector", "seo_optimizer"],
        "skills": [
            {
                "id": "publish_content",
                "name": "Publish Content",
                "description": "Format and publish articles to the CMS with proper categories, tags, and metadata",
                "tags": ["publish", "cms", "format"],
                "examples": ["Publish this article", "Schedule for publication"],
            },
            {
                "id": "seo_optimize",
                "name": "SEO Optimize",
                "description": "Optimize content for search engines with keywords, meta descriptions, and structured data",
                "tags": ["seo", "keywords", "optimization"],
                "examples": ["Optimize for SEO", "Add meta tags and keywords"],
            },
            {
                "id": "schedule",
                "name": "Schedule Publication",
                "description": "Manage the editorial calendar and schedule content for optimal publishing times",
                "tags": ["schedule", "calendar", "timing"],
                "examples": ["Schedule for tomorrow morning", "Find the best time to publish"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
        },
    },

    "editor_in_chief": {
        "name": "Redactor Jefe",
        "description": "Supervisa el flujo editorial, asigna artículos a los periodistas, gestiona prioridades y garantiza una calidad de contenido consistente en todas las publicaciones.",
        "default_tools": ["editorial_dashboard"],
        "skills": [
            {
                "id": "assign_stories",
                "name": "Assign Stories",
                "description": "Review incoming news items and assign them to journalists based on beat expertise and workload",
                "tags": ["assign", "workflow", "management"],
                "examples": ["Assign this story to a journalist", "Who should cover this topic?"],
            },
            {
                "id": "editorial_standup",
                "name": "Editorial Standup",
                "description": "Summarize the current state of the editorial pipeline: what's in progress, what's stuck, what's ready to publish",
                "tags": ["standup", "summary", "status"],
                "examples": ["Give me a pipeline summary", "What's the status of today's content?"],
            },
            {
                "id": "manage_priorities",
                "name": "Manage Priorities",
                "description": "Reprioritize stories based on breaking news, reader interest, and editorial strategy",
                "tags": ["priority", "strategy", "breaking"],
                "examples": ["Reprioritize the content queue", "This story needs to be fast-tracked"],
            },
            {
                "id": "quality_oversight",
                "name": "Quality Oversight",
                "description": "Review final content for editorial quality and brand alignment before major publications",
                "tags": ["quality", "brand", "oversight"],
                "examples": ["Final review before publishing", "Check quality of today's articles"],
            },
        ],
        "capabilities": {
            "streaming": False,
            "push_notifications": True,
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
