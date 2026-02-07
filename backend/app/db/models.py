import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from app.db.database import Base


# Renamed: kept for orchestrator/swarm internal use only
class SoftwareDevStatus(str, enum.Enum):
    BACKLOG = "backlog"
    READY_FOR_BREAKDOWN = "ready_for_breakdown"
    IN_BREAKDOWN = "in_breakdown"
    TASKS_IN_REVIEW = "tasks_in_review"
    IN_DEVELOPMENT = "in_development"
    IN_QA = "in_qa"
    DONE = "done"


# Backward-compat alias so existing imports like `from app.db.models import StoryStatus` still work
StoryStatus = SoftwareDevStatus


class TaskStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"  # Tech lead is reviewing
    READY_FOR_DEVELOPMENT = "ready_for_development"
    IN_PROGRESS = "in_progress"
    CODE_REVIEW = "code_review"
    CODE_REVIEW_IN_PROGRESS = "code_review_in_progress"  # Code reviewer is reviewing
    READY_FOR_QA = "ready_for_qa"
    QA_IN_PROGRESS = "qa_in_progress"
    DONE = "done"


class AgentType(str, enum.Enum):
    PRODUCT_OWNER = "product_owner"
    TECH_LEAD = "tech_lead"
    DEVELOPER = "developer"
    CODE_REVIEWER = "code_reviewer"
    QA = "qa"
    SCRUM_MASTER = "scrum_master"
    CLIENT = "client"  # Human user proxy for A2A communication


class PipelineConfig(Base):
    """Board configuration - defines the Kanban board columns."""
    __tablename__ = "pipeline_configs"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    columns = Column(JSON, nullable=False)  # List of {key, label, color, position}
    agent_automation = Column(Boolean, default=True)
    item_noun = Column(String(50), default="Story")
    has_tasks = Column(Boolean, default=True)
    sub_item_noun = Column(String(50), default="Task")
    input_noun = Column(String(50), default="PRD")
    epic_noun = Column(String(50), default="Epic")
    input_placeholder = Column(Text, nullable=True)
    sub_item_statuses = Column(JSON, nullable=True)
    item_source = Column(String(20), default="internal")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stories = relationship("Story", back_populates="board", cascade="all, delete-orphan")
    agents = relationship("DynamicAgent", back_populates="board", cascade="all, delete-orphan")
    epics = relationship("Epic", back_populates="board", cascade="all, delete-orphan")


class Epic(Base):
    """Grouping entity above stories (Epic/Position/Account/Threat Category)."""
    __tablename__ = "epics"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("pipeline_configs.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="open", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    board = relationship("PipelineConfig", back_populates="epics")
    stories = relationship("Story", back_populates="epic")


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("pipeline_configs.id"), nullable=False)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    status = Column(String(50), default="backlog", nullable=False)
    priority = Column(Integer, default=0)
    prd_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def input_content(self):
        """Alias for prd_content for generic input system."""
        return self.prd_content

    @input_content.setter
    def input_content(self, value):
        self.prd_content = value

    board = relationship("PipelineConfig", back_populates="stories")
    epic = relationship("Epic", back_populates="stories")
    tasks = relationship("Task", back_populates="story", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="story", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    implementation_notes = Column(Text, nullable=True)
    test_scenarios = Column(Text, nullable=True)
    status = Column(String(50), default="draft", nullable=False)
    assigned_agent = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    story = relationship("Story", back_populates="tasks")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    agent_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    extra_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    story = relationship("Story", back_populates="comments")
    task = relationship("Task", back_populates="comments")


class AgentMessage(Base):
    """Chat messages between agents - the 'Slack' layer."""
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    from_agent = Column(String(50), nullable=False)
    to_agent = Column(String(50), nullable=True)  # None = broadcast to all
    content = Column(Text, nullable=False)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    message_type = Column(String(50), default="chat")  # chat, handoff, question, approval
    created_at = Column(DateTime, default=datetime.utcnow)


class DynamicAgent(Base):
    """User-created agents that can be added/removed dynamically."""
    __tablename__ = "dynamic_agents"

    id = Column(String(50), primary_key=True)  # e.g., "recruiter_3"
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    role = Column(String(50), nullable=True)  # Agent role within board (e.g., "recruiter")
    template = Column(String(50), nullable=True)  # Template used to create
    board_id = Column(Integer, ForeignKey("pipeline_configs.id"), nullable=True)
    tools = Column(JSON, default=[])  # Selected tools from basket
    skills = Column(JSON, default=[])  # Custom skills
    capabilities = Column(JSON, default={})  # Agent capabilities
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    board = relationship("PipelineConfig", back_populates="agents")


class CustomTool(Base):
    """User-defined tools that can be assigned to dynamic agents."""
    __tablename__ = "custom_tools"

    id = Column(String(50), primary_key=True)  # e.g., "my_security_tool"
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # security, code, testing, etc.
    capabilities = Column(JSON, default=[])  # List of capability strings
    config = Column(JSON, default={})  # Tool-specific configuration
    is_builtin = Column(Boolean, default=False)  # False for user-created
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
