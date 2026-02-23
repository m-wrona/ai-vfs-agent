"""Boot tools: fs_read and optional AgentFS/Daytona + skill tools."""

import json
from .fs import FS_READ_SCHEMA, FS_WRITE_SCHEMA, execute_fs_read, execute_fs_write

__all__ = ["FS_READ_SCHEMA", "FS_WRITE_SCHEMA", "execute_fs_read", "execute_fs_write", "get_tools", "execute_tool"]


EXECUTE_CODE_SCHEMA = {
    "description": "Execute Python in sandbox. Import skills: from skills.products import products, get_product_by_id; from skills.orders import orders, get_orders_by_product. Use print() for output. Use open() to write files for read_output.",
    "parameters": {
        "type": "object",
        "properties": {"code": {"type": "string", "description": "Python code to execute"}},
        "required": ["code"],
        "additionalProperties": False,
    },
}

LIST_SKILLS_SCHEMA = {
    "description": "List available skills. Start here to discover capabilities.",
    "parameters": {"type": "object", "properties": {}, "required": []},
    "additionalProperties": False,
}

GET_SKILL_SCHEMA = {
    "description": "Get Python API schema for a skill. Load before using in execute_code.",
    "parameters": {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Skill name from list_skills"}},
        "required": ["name"],
        "additionalProperties": False,
    },
}

READ_OUTPUT_SCHEMA = {
    "description": "Read a file created by execute_code in the sandbox (path relative to workspace, e.g. result.txt or workspace/out.txt).",
    "parameters": {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "File path relative to sandbox workspace"}},
        "required": ["path"],
        "additionalProperties": False,
    },
}

SHELL_SCHEMA = {
    "description": "Run a shell command in the sandbox (for debugging).",
    "parameters": {
        "type": "object",
        "properties": {"command": {"type": "string", "description": "Shell command to run"}},
        "required": ["command"],
        "additionalProperties": False,
    },
}


def get_tools(workspace_root: str, daytona_enabled: bool = False):
    """Return list of tool definitions for OpenAI and the executor."""
    tools = [
        {"type": "function", "function": {"name": "fs_read", "description": FS_READ_SCHEMA["description"], "parameters": FS_READ_SCHEMA["parameters"]}},
        {"type": "function", "function": {"name": "fs_write", "description": FS_WRITE_SCHEMA["description"], "parameters": FS_WRITE_SCHEMA["parameters"]}},
    ]
    if daytona_enabled:
        tools.extend([
            {"type": "function", "function": {"name": "list_skills", "description": LIST_SKILLS_SCHEMA["description"], "parameters": LIST_SKILLS_SCHEMA["parameters"]}},
            {"type": "function", "function": {"name": "get_skill", "description": GET_SKILL_SCHEMA["description"], "parameters": GET_SKILL_SCHEMA["parameters"]}},
            {"type": "function", "function": {"name": "execute_code", "description": EXECUTE_CODE_SCHEMA["description"], "parameters": EXECUTE_CODE_SCHEMA["parameters"]}},
            {"type": "function", "function": {"name": "read_output", "description": READ_OUTPUT_SCHEMA["description"], "parameters": READ_OUTPUT_SCHEMA["parameters"]}},
            {"type": "function", "function": {"name": "shell", "description": SHELL_SCHEMA["description"], "parameters": SHELL_SCHEMA["parameters"]}},
        ])
    return tools


def execute_tool(name: str, arguments: dict, workspace_root: str, daytona_enabled: bool = False):
    """Execute a tool by name. Raises KeyError if unknown."""
    if name == "fs_read":
        return execute_fs_read(workspace_root=workspace_root, **arguments)
    if name == "fs_write":
        return execute_fs_write(workspace_root=workspace_root, **arguments)
    if not daytona_enabled:
        raise KeyError(f"Unknown tool: {name}")
    if name == "list_skills":
        from ..skill_registry import list_skills as _list_skills
        return json.dumps({"skills": _list_skills(workspace_root)}, indent=2)
    if name == "get_skill":
        from ..skill_registry import get_skill_schema
        schema = get_skill_schema(arguments.get("name", ""), workspace_root)
        if not schema:
            return json.dumps({"error": "Skill not found: " + arguments.get("name", "")})
        return json.dumps(schema, indent=2)
    if name == "execute_code":
        from ..sandbox import run_code_in_sandbox
        return run_code_in_sandbox(arguments.get("code", ""))
    if name == "read_output":
        from ..sandbox import download_file
        return download_file(arguments.get("path", ""))
    if name == "shell":
        from ..sandbox import exec_command
        return exec_command(arguments.get("command", ""))
    raise KeyError(f"Unknown tool: {name}")
