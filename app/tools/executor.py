from typing import Any

from app.tools.registry import ToolRegistry


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""


class ToolExecutor:
    """
    Execute tools registered in ToolRegistry.
    """

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute(
        self,
        name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a registered tool.
        """

        # Get tool from registry
        tool = self.registry.get(name)

        # Tool does not exist
        if tool is None:
            raise ToolExecutionError(
                f"Tool '{name}' is not registered."
            )

        # Tool must be callable
        if not callable(tool):
            raise ToolExecutionError(
                f"Tool '{name}' is not callable."
            )

        # Execute
        try:
            return tool(
                *args,
                **kwargs,
            )

        except Exception as exc:
            raise ToolExecutionError(
                f"Tool '{name}' execution failed: {exc}"
            ) from exc