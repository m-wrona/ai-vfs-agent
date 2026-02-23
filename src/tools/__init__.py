"""Boot tools: fs_read and optional AgentFS/Daytona integrations."""

from .fs import FS_READ_SCHEMA, execute_fs_read

__all__ = ["FS_READ_SCHEMA", "execute_fs_read", "get_tools", "execute_tool"]


EXECUTE_CODE_SCHEMA = {
    "description": "Run Python code in an isolated Daytona sandbox. Use for calculations, processing, or running scripts. Code runs in isolation; use print() for output.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute (e.g. print(1+1))"},
        },
        "required": ["code"],
        "additionalProperties": False,
    },
}


def get_tools(workspace_root: str, daytona_enabled: bool = False):
    """Return list of tool definitions for OpenAI and the executor."""
    tools = [
        {"type": "function", "function": {"name": "fs_read", "description": FS_READ_SCHEMA["description"], "parameters": FS_READ_SCHEMA["parameters"]}},
    ]
    if daytona_enabled:
        tools.append({
            "type": "function",
            "function": {"name": "execute_code", "description": EXECUTE_CODE_SCHEMA["description"], "parameters": EXECUTE_CODE_SCHEMA["parameters"]},
        })
    return tools


def execute_tool(name: str, arguments: dict, workspace_root: str, daytona_enabled: bool = False):
    """Execute a tool by name. Raises KeyError if unknown."""
    if name == "fs_read":
        return execute_fs_read(workspace_root=workspace_root, **arguments)
    if name == "execute_code" and daytona_enabled:
        from ..sandbox import run_code_in_sandbox
        code = arguments.get("code", "")
        return run_code_in_sandbox(code)
    raise KeyError(f"Unknown tool: {name}")
