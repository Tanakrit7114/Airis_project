import pytest

from app.tools.registry import ToolRegistry
from app.tools.executor import (
    ToolExecutor,
    ToolExecutionError,
)


def add(a, b):
    return a + b


def broken_tool():
    raise RuntimeError("Something went wrong")


def test_executor():
    registry = ToolRegistry()

    registry.register("add", add)

    executor = ToolExecutor(registry)

    result = executor.execute(
        "add",
        10,
        20,
    )

    assert result == 30


def test_missing_tool():
    registry = ToolRegistry()

    executor = ToolExecutor(registry)

    with pytest.raises(ToolExecutionError):
        executor.execute("unknown")


def test_tool_error():
    registry = ToolRegistry()

    registry.register(
        "broken",
        broken_tool,
    )

    executor = ToolExecutor(registry)

    with pytest.raises(ToolExecutionError):
        executor.execute("broken")
