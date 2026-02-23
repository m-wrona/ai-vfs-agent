"""Simple agent loop: user prompt → LLM → tool calls (e.g. fs_read) → result → response."""

import json
from openai import OpenAI

from .config import get_config
from .tools import get_tools, execute_tool


def _system_prompt() -> str:
    return """You are a helpful assistant that can read and write workspace files and use skills.

## FILES
Use fs_read to list (path ".") or read files (path "filename" or "dir/file"). Use "lines" for a line range.
Use fs_write to create or overwrite files (path, content). Parent directories are created if needed.

## SKILLS WORKFLOW (when skill tools are available)
1. Use list_skills to see available capabilities (e.g. fs_read, fs_write)
2. Use get_skill to load a skill's API (parameters, usage)
3. Call the tool (e.g. fs_read, fs_write) with the parameters described
4. When execute_code is available: run Python in sandbox; use read_output to read files your code created

## RULES
- For file/directory questions, use fs_read first
- To create or change a file, use fs_write with path and content
- For skill-based tasks, discover skills first; load schemas before calling tools
- Be concise and efficient
"""


def run_agent_loop(
    user_input: str,
    *,
    api_key: str,
    model: str,
    workspace_root: str,
    max_iterations: int = 10,
    daytona_enabled: bool = False,
):
    """Run one agent turn: possibly multiple tool calls, then return final text."""
    client = OpenAI(api_key=api_key)
    openai_tools = get_tools(workspace_root, daytona_enabled=daytona_enabled)
    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": user_input},
    ]

    for _ in range(max_iterations):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=openai_tools,
            tool_choice="auto",
        )
        choice = resp.choices[0]
        if not choice.message.tool_calls:
            return choice.message.content or ""

        messages.append(choice.message)
        for tc in choice.message.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            try:
                result = execute_tool(name, args, workspace_root, daytona_enabled=daytona_enabled)
            except Exception as e:
                result = json.dumps({"error": str(e)})
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return "[Max iterations reached]"


def main():
    cfg = get_config()
    if not cfg["openai_api_key"]:
        print("Set OPENAI_API_KEY or add openai.api_key in config.yaml")
        return
    workspace = cfg["workspace_root"]
    daytona_key = (cfg.get("daytona_api_key") or "").strip()
    daytona_enabled = False
    sandbox_id = None

    if daytona_key:
        try:
            from .sandbox import init_sandbox, get_sandbox, destroy_sandbox
            init_sandbox(daytona_key, workspace)
            sb = get_sandbox()
            daytona_enabled = sb is not None
            if sb:
                sandbox_id = getattr(sb, "id", None) or "(Daytona sandbox)"
        except Exception as e:
            print(f"Daytona sandbox unavailable: {e}")
            print("Continuing without isolated code execution.\n")

    print(f"Workspace: {workspace}")
    if daytona_enabled:
        print(f"Code runs in isolation: Daytona sandbox {sandbox_id}")
        print("Tools: fs_read, list_skills, get_skill, execute_code, read_output, shell")
    else:
        print("Tools: fs_read, fs_write (list/read/write files)")
    print('Type "exit" to quit.\n')

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if user_input.lower() == "exit":
                break
            if not user_input:
                continue
            try:
                text = run_agent_loop(
                    user_input,
                    api_key=cfg["openai_api_key"],
                    model=cfg["openai_model"],
                    workspace_root=workspace,
                    max_iterations=cfg["max_iterations"],
                    daytona_enabled=daytona_enabled,
                )
                print(f"\nAssistant: {text}\n")
            except Exception as e:
                print(f"\nError: {e}\n")
    finally:
        if daytona_enabled:
            try:
                from .sandbox import destroy_sandbox
                destroy_sandbox()
                print("Daytona sandbox destroyed.")
            except Exception:
                pass


if __name__ == "__main__":
    main()
