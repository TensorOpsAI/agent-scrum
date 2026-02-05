from pydantic import BaseModel, Field
from typing import Any, Literal
from enum import Enum


class A2ATaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str] = []
    examples: list[str] = []


class AgentCapabilities(BaseModel):
    streaming: bool = False
    push_notifications: bool = False
    state_transition_history: bool = True


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    skills: list[AgentSkill] = []
    default_input_modes: list[str] = ["text"]
    default_output_modes: list[str] = ["text"]


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class DataPart(BaseModel):
    type: Literal["data"] = "data"
    data: dict[str, Any]


Part = TextPart | DataPart


class Message(BaseModel):
    role: Literal["user", "agent"]
    parts: list[Part]


class A2ATask(BaseModel):
    id: str
    session_id: str | None = None
    state: A2ATaskState = A2ATaskState.SUBMITTED
    messages: list[Message] = []
    artifacts: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}


class TaskSendParams(BaseModel):
    id: str
    session_id: str | None = None
    message: Message
    metadata: dict[str, Any] = {}


class TaskGetParams(BaseModel):
    id: str


class TaskCancelParams(BaseModel):
    id: str


# JSON-RPC 2.0 Request/Response schemas
class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: str | int
    method: str
    params: dict[str, Any] | None = None


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Any | None = None


class JSONRPCResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: str | int
    result: Any | None = None
    error: JSONRPCError | None = None


# A2A Error codes
class A2AErrorCodes:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    TASK_NOT_FOUND = -32001
    TASK_CANCELED = -32002
    AGENT_BUSY = -32003
