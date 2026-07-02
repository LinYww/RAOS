"""Startup helpers that seed persistent runtime metadata."""

from sqlalchemy.orm import Session

from app.models.tool import ToolDefinition
from app.repositories.tools import ToolRepository
from app.tools.bootstrap import get_tool_registry


def bootstrap_builtin_tools(session: Session) -> None:
    """Mirror built-in tool definitions into the database."""
    repository = ToolRepository(session)
    for definition in get_tool_registry().definitions():
        repository.upsert_definition(
            ToolDefinition(
                name=definition.name,
                description=definition.description,
                input_schema=definition.input_schema,
                output_schema=definition.output_schema,
                permission_scope=definition.permission_scope,
                timeout_seconds=definition.timeout_seconds,
                audit_fields=definition.audit_fields,
                enabled=True,
            )
        )
