# ai-vfs-agent

An LLM agent that uses a **virtual workspace filesystem** (read/write via `fs_read`/`fs_write`) and an optional **sandbox** (Daytona) to run code. 
The agent discovers **built-in and dynamic skills** (`list_skills` / `get_skill`); domain skills (e.g. products, orders) live in `workspace/skills/*.py` and are used inside the sandbox via `execute_code`. 
Each turn returns a **Plan** (what it did and which skills it used) and a **Result** (the answer or a clear failure message).


Tools:

* [AgentFS](https://www.agentfs.ai) — virtual filesystem and tooling for AI agents. Not wired in by default; install `agentfs-sdk` and extend `src/tools/` to use AgentFS instead of or alongside the built-in `fs_read`/`fs_write` for workspace access.
* [Daytona](https://www.daytona.io) — when configured (`DAYTONA_API_KEY`), the agent runs `execute_code` in an isolated cloud sandbox: the workspace is synced in, Python runs there (so skills and file access are confined), and you get `read_output` / `shell`. Without Daytona, code runs locally in a subprocess (same skills, no isolation).


```
User Prompt
     ↓
Agent Harness
     ↓
LLM (plan) <- Tool capabilities
     ↓
Tool call (i.e. fs_read)
     ↓
Execution (filesystem)
     ↓
Result returns to LLM
     ↓
Final response
```

## Local development

Minimal Python agent that reads files from a directory using boot tools.

1. **Config (YAML + env)**  
   Copy `config.example.yaml` to `config.yaml` and set:
   - `openai.api_key` (or `OPENAI_API_KEY`)
   - `daytona.api_key` (or `DAYTONA_API_KEY`) — optional, for future sandbox tools  
   Set `workspace.root` to the directory the agent can read (default `./workspace`).

2. **Boot tools**  
   - `fs_read`: list directory or read file under the workspace root (path `"."` or `"path/to/file"`).  
   Optional: install `agentfs-sdk` / `daytona-sdk` and extend `src/tools/` to add AgentFS or Daytona tools.

3. **Run the agent**  
   ```bash
   python3 -m venv .venv && source .venv/bin/activate  
   pip install -r requirements.txt
   python run_agent.py
   ```  

# Docs

* [Solving a Million-Step LLM Task with Zero Errors](https://arxiv.org/abs/2511.09030)