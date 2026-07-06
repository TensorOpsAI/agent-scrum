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
        "template_id": "publisher",
        "name": "Redacción",
        "columns": [
            {"key": "inbox", "label": "Bandeja de entrada", "color": "bg-gray-600", "position": 0},
            {"key": "writing", "label": "Redacción", "color": "bg-blue-600", "position": 1},
            {"key": "editing", "label": "Edición", "color": "bg-purple-600", "position": 2},
            {"key": "creatives", "label": "Creativos", "color": "bg-pink-600", "position": 3},
            {"key": "ready_to_publish", "label": "Listo para publicar", "color": "bg-yellow-600", "position": 4},
            {"key": "published", "label": "Publicado", "color": "bg-green-600", "position": 5},
        ],
        "agent_automation": True,
        "item_noun": "Artículo",
        "has_tasks": True,
        "sub_item_noun": "Sección",
        "input_noun": "Brief de noticias",
        "epic_noun": "Tema",
        "input_placeholder": "Pega aquí tu brief de noticias o tema...\n\nEjemplo:\n# Tema: La IA en la sanidad\n## Novedades clave\n- La FDA aprueba la primera herramienta de diagnóstico con IA\n- Las principales redes hospitalarias adoptan el triaje con IA\n## Enfoque\nCentrarse en los resultados para el paciente y las implicaciones de seguridad",
        "sub_item_statuses": ["pending", "in_progress", "review", "done"],
        "item_source": "internal",
        "intake_agent": "news_curator",
        "manager_role": "editor_in_chief",
        "agents": [
            {"role": "news_curator", "name": "Curador de Noticias", "description": "Explora fuentes de noticias y temas de tendencia, selecciona elementos de interés para su cobertura", "tools": ["rss_reader", "trend_analyzer"]},
            {"role": "journalist", "name": "Periodista", "description": "Redacta artículos a partir de las noticias seleccionadas y los prepara para su publicación", "tools": ["article_writer", "fact_checker"]},
            {"role": "editor", "name": "Editor", "description": "Revisa los artículos en cuanto a calidad, precisión, tono y estándares editoriales", "tools": ["grammar_checker", "plagiarism_detector"]},
            {"role": "creative_director", "name": "Director Creativo", "description": "Selecciona o genera imágenes, miniaturas y elementos creativos para los artículos", "tools": ["image_generator", "asset_library"]},
            {"role": "publisher_agent", "name": "Publicador", "description": "Da formato y publica el contenido final, gestiona el calendario de publicación", "tools": ["cms_connector", "seo_optimizer"]},
            {"role": "editor_in_chief", "name": "Redactor Jefe", "description": "Supervisa el flujo editorial, asigna artículos y gestiona prioridades (gestor)", "tools": ["editorial_dashboard"], "is_active": True},
        ],
    },
]


# ============================================================================
# Workflow Rules per Template
# ============================================================================
# Maps column keys to (agent_role, action, next_status) for the swarm to dispatch.

TEMPLATE_WORKFLOWS = {
    "publisher": {
        "story_handlers": {
            "writing": ("journalist", "write_article", "editing"),
            "editing": ("editor", "review_article", "creatives"),
            "creatives": ("creative_director", "create_visuals", "ready_to_publish"),
            "ready_to_publish": ("publisher_agent", "publish", "published"),
        },
        "task_handlers": {
            "pending": ("journalist", "draft_section", "in_progress"),
            "in_progress": ("editor", "review_section", "review"),
            "review": ("creative_director", "attach_media", "done"),
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
