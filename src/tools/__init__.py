"""Boot tools: fs_read and optional AgentFS/Daytona integrations."""

from .fs import FS_READ_SCHEMA, execute_fs_read

__all__ = ["FS_READ_SCHEMA", "execute_fs_read", "get_tools", "execute_tool"]


def get_tools(workspace_root: str):
    """Return list of tool definitions for OpenAI and the executor."""
    tools = [
        {"type": "function", "function": {"name": "fs_read", "description": FS_READ_SCHEMA["description"], "parameters": FS_READ_SCHEMA["parameters"]}},
    ]
    return tools


def execute_tool(name: str, arguments: dict, workspace_root: str):
    """Execute a tool by name. Raises KeyError if unknown."""
    if name == "fs_read":
        return execute_fs_read(workspace_root=workspace_root, **arguments)
    raise KeyError(f"Unknown tool: {name}")
