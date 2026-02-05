"""
Agent chat service - handles the "Slack" layer of agent communication.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentMessage, AgentType
from app.api.websocket.manager import broadcast_agent_chat


# Agent display names for natural chat
AGENT_NAMES = {
    AgentType.PRODUCT_OWNER: "Product Owner",
    AgentType.TECH_LEAD: "Tech Lead",
    AgentType.DEVELOPER: "Developer",
    AgentType.CODE_REVIEWER: "Code Reviewer",
    AgentType.QA: "QA",
    AgentType.CLIENT: "Human",
}


async def send_chat_message(
    from_agent: AgentType,
    content: str,
    db: AsyncSession,
    to_agent: AgentType | None = None,
    story_id: int | None = None,
    task_id: int | None = None,
    message_type: str = "chat",
) -> AgentMessage:
    """Send a chat message from one agent to another (or broadcast to all)."""
    message = AgentMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        content=content,
        story_id=story_id,
        task_id=task_id,
        message_type=message_type,
    )
    db.add(message)
    await db.flush()
    await db.commit()  # Commit immediately so message persists

    # Broadcast to connected clients
    await broadcast_agent_chat({
        "id": message.id,
        "from_agent": from_agent.value,
        "from_agent_name": AGENT_NAMES.get(from_agent, from_agent.value),
        "to_agent": to_agent.value if to_agent else None,
        "to_agent_name": AGENT_NAMES.get(to_agent) if to_agent else None,
        "content": content,
        "story_id": story_id,
        "task_id": task_id,
        "message_type": message_type,
        "created_at": message.created_at.isoformat(),
    })

    return message


# Pre-built message templates for common scenarios
class ChatTemplates:
    """Natural language templates for agent chat messages."""

    @staticmethod
    def prd_received(story_count: int) -> str:
        return f"Hey team! 👋 I've just analyzed a new PRD and created {story_count} {'story' if story_count == 1 else 'stories'}. Check out the board for details!"

    @staticmethod
    def story_ready_for_breakdown(story_id: int, story_title: str) -> str:
        return f"@Developer STORY-{story_id} \"{story_title}\" is ready for breakdown. Can you take a look and create the tasks?"

    @staticmethod
    def breakdown_complete(story_id: int, task_count: int) -> str:
        return f"@Tech Lead I've broken down STORY-{story_id} into {task_count} tasks. PTAL when you get a chance! 🔍"

    @staticmethod
    def tasks_review_started(story_id: int) -> str:
        return f"Looking at the tasks for STORY-{story_id} now..."

    @staticmethod
    def tasks_approved(story_id: int) -> str:
        return f"✅ LGTM! Tasks for STORY-{story_id} are approved. Moving to development!"

    @staticmethod
    def tasks_need_changes(story_id: int, feedback: str) -> str:
        return f"@Developer Left some comments on STORY-{story_id}. {feedback}"

    @staticmethod
    def task_ready_for_dev(task_id: int, task_title: str) -> str:
        return f"Starting work on TASK-{task_id}: \"{task_title}\" 💻"

    @staticmethod
    def implementation_done(task_id: int) -> str:
        return f"@Code Reviewer TASK-{task_id} implementation is done! I've added notes on the ticket. Ready for review 🙏"

    @staticmethod
    def code_review_started(task_id: int) -> str:
        return f"Reviewing TASK-{task_id} now..."

    @staticmethod
    def code_review_approved(task_id: int) -> str:
        return f"✅ TASK-{task_id} looks good! Clean code, nice work. Approved!"

    @staticmethod
    def code_review_changes(task_id: int, feedback: str) -> str:
        return f"@Developer Left feedback on TASK-{task_id}. {feedback}"

    @staticmethod
    def ready_for_qa(task_id: int) -> str:
        return f"@QA TASK-{task_id} passed code review and is ready for testing! 🧪"

    @staticmethod
    def qa_started(task_id: int) -> str:
        return f"Running test scenarios for TASK-{task_id}... 🔬"

    @staticmethod
    def qa_passed(task_id: int) -> str:
        return f"✅ TASK-{task_id} passed all tests! Moving to Done. Great work team! 🎉"

    @staticmethod
    def qa_failed(task_id: int, issues: str) -> str:
        return f"@Developer Found some issues with TASK-{task_id}: {issues}. See the ticket for details."

    @staticmethod
    def story_complete(story_id: int, story_title: str) -> str:
        return f"🎉 STORY-{story_id} \"{story_title}\" is complete! All tasks done and tested. Nice teamwork everyone!"
