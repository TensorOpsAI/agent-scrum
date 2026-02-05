from typing import Any, Callable, Coroutine
from app.schemas.a2a import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    A2AErrorCodes,
    A2ATask,
    A2ATaskState,
    TaskSendParams,
    TaskGetParams,
    TaskCancelParams,
    Message,
    TextPart,
)


class A2AProtocolHandler:
    """Handles JSON-RPC 2.0 protocol for A2A communication."""

    def __init__(self):
        self._tasks: dict[str, A2ATask] = {}
        self._handlers: dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}

    def register_handler(
        self, method: str, handler: Callable[..., Coroutine[Any, Any, Any]]
    ):
        """Register a handler for a specific JSON-RPC method."""
        self._handlers[method] = handler

    async def handle_request(self, request_data: dict) -> JSONRPCResponse:
        """Process a JSON-RPC 2.0 request and return a response."""
        try:
            request = JSONRPCRequest(**request_data)
        except Exception as e:
            return JSONRPCResponse(
                id=request_data.get("id", 0),
                error=JSONRPCError(
                    code=A2AErrorCodes.PARSE_ERROR,
                    message=f"Invalid request format: {str(e)}",
                ),
            )

        method = request.method
        params = request.params or {}

        # Built-in methods
        if method == "tasks/send":
            return await self._handle_task_send(request.id, params)
        elif method == "tasks/get":
            return await self._handle_task_get(request.id, params)
        elif method == "tasks/cancel":
            return await self._handle_task_cancel(request.id, params)

        # Custom handlers
        if method in self._handlers:
            try:
                result = await self._handlers[method](params)
                return JSONRPCResponse(id=request.id, result=result)
            except Exception as e:
                return JSONRPCResponse(
                    id=request.id,
                    error=JSONRPCError(
                        code=A2AErrorCodes.INTERNAL_ERROR,
                        message=str(e),
                    ),
                )

        return JSONRPCResponse(
            id=request.id,
            error=JSONRPCError(
                code=A2AErrorCodes.METHOD_NOT_FOUND,
                message=f"Method not found: {method}",
            ),
        )

    async def _handle_task_send(
        self, request_id: str | int, params: dict
    ) -> JSONRPCResponse:
        """Handle tasks/send method - send a message to create or continue a task."""
        try:
            send_params = TaskSendParams(**params)
        except Exception as e:
            return JSONRPCResponse(
                id=request_id,
                error=JSONRPCError(
                    code=A2AErrorCodes.INVALID_PARAMS,
                    message=f"Invalid params: {str(e)}",
                ),
            )

        task_id = send_params.id

        # Get or create task
        if task_id in self._tasks:
            task = self._tasks[task_id]
        else:
            task = A2ATask(
                id=task_id,
                session_id=send_params.session_id,
                state=A2ATaskState.SUBMITTED,
                metadata=send_params.metadata,
            )
            self._tasks[task_id] = task

        # Add the message
        task.messages.append(send_params.message)

        # If there's a registered handler for message processing, call it
        if "process_message" in self._handlers:
            try:
                response_message = await self._handlers["process_message"](task)
                if response_message:
                    task.messages.append(response_message)
            except Exception as e:
                task.state = A2ATaskState.FAILED
                return JSONRPCResponse(
                    id=request_id,
                    error=JSONRPCError(
                        code=A2AErrorCodes.INTERNAL_ERROR,
                        message=f"Processing error: {str(e)}",
                    ),
                )

        return JSONRPCResponse(id=request_id, result=task.model_dump())

    async def _handle_task_get(
        self, request_id: str | int, params: dict
    ) -> JSONRPCResponse:
        """Handle tasks/get method - retrieve a task's current state."""
        try:
            get_params = TaskGetParams(**params)
        except Exception as e:
            return JSONRPCResponse(
                id=request_id,
                error=JSONRPCError(
                    code=A2AErrorCodes.INVALID_PARAMS,
                    message=f"Invalid params: {str(e)}",
                ),
            )

        task_id = get_params.id

        if task_id not in self._tasks:
            return JSONRPCResponse(
                id=request_id,
                error=JSONRPCError(
                    code=A2AErrorCodes.TASK_NOT_FOUND,
                    message=f"Task not found: {task_id}",
                ),
            )

        return JSONRPCResponse(
            id=request_id, result=self._tasks[task_id].model_dump()
        )

    async def _handle_task_cancel(
        self, request_id: str | int, params: dict
    ) -> JSONRPCResponse:
        """Handle tasks/cancel method - cancel a running task."""
        try:
            cancel_params = TaskCancelParams(**params)
        except Exception as e:
            return JSONRPCResponse(
                id=request_id,
                error=JSONRPCError(
                    code=A2AErrorCodes.INVALID_PARAMS,
                    message=f"Invalid params: {str(e)}",
                ),
            )

        task_id = cancel_params.id

        if task_id not in self._tasks:
            return JSONRPCResponse(
                id=request_id,
                error=JSONRPCError(
                    code=A2AErrorCodes.TASK_NOT_FOUND,
                    message=f"Task not found: {task_id}",
                ),
            )

        task = self._tasks[task_id]
        task.state = A2ATaskState.CANCELED

        return JSONRPCResponse(id=request_id, result=task.model_dump())

    def get_task(self, task_id: str) -> A2ATask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def update_task_state(self, task_id: str, state: A2ATaskState):
        """Update a task's state."""
        if task_id in self._tasks:
            self._tasks[task_id].state = state

    def add_task_message(self, task_id: str, role: str, text: str):
        """Add a message to a task."""
        if task_id in self._tasks:
            message = Message(role=role, parts=[TextPart(text=text)])
            self._tasks[task_id].messages.append(message)
