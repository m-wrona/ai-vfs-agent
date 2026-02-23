"""Simple agent loop: user prompt → LLM → tool calls (e.g. fs_read) → result → response."""

import json
from openai import OpenAI

from .config import get_config
from .tools import get_tools, execute_tool


SYSTEM_PROMPT = """You are a helpful assistant that can read files from the workspace.

Use the fs_read tool to:
- List the workspace root: use path "."
- Read a file: use path like "filename.txt" or "src/main.py"
- Optionally use "lines" for a line range (e.g. "10-50")

Be concise. When the user asks about files or a directory, use fs_read first to explore or read content."""


def run_agent_loop(
    user_input: str,
    *,
    api_key: str,
    model: str,
    workspace_root: str,
    max_iterations: int = 10,
):
    """Run one agent turn: possibly multiple tool calls, then return final text."""
    client = OpenAI(api_key=api_key)
    openai_tools = get_tools(workspace_root)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
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

        for tc in choice.message.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            try:
                result = execute_tool(name, args, workspace_root)
            except Exception as e:
                result = json.dumps({"error": str(e)})
            messages.append(choice.message)
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
    print(f"Workspace: {workspace}")
    print("Tools: fs_read (list dir / read file)")
    print('Type "exit" to quit.\n')

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
            )
            print(f"\nAssistant: {text}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
