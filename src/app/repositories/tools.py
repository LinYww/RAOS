"""Persistence operations for tool definitions and invocations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tool import ToolDefinition, ToolInvocation


class ToolRepository:
    """Manage persisted tool metadata and invocation audit rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_definition(self, definition: ToolDefinition) -> ToolDefinition:
        """Insert or refresh a built-in tool definition by name."""
        existing = self._session.scalars(
            select(ToolDefinition).where(ToolDefinition.name == definition.name)
        ).first()
        if existing is None:
            self._session.add(definition)
            self._session.flush()
            return definition

        existing.description = definition.description
        existing.input_schema = definition.input_schema
        existing.output_schema = definition.output_schema
        existing.permission_scope = definition.permission_scope
        existing.timeout_seconds = definition.timeout_seconds
        existing.audit_fields = definition.audit_fields
        existing.enabled = definition.enabled
        self._session.flush()
        return existing

    def get_by_name(self, tool_name: str) -> ToolDefinition | None:
        """Fetch a tool definition by its public name."""
        return self._session.scalars(
            select(ToolDefinition).where(ToolDefinition.name == tool_name)
        ).first()

    def create_invocation(self, invocation: ToolInvocation) -> ToolInvocation:
        """Persist one tool invocation audit record."""
        self._session.add(invocation)
        self._session.flush()
        return invocation
