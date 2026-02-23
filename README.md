# ai-vfs-agent

Agents co-operating using virtual FS and sandbox.

Tools:

* [AgentFS](https://www.agentfs.ai)
* [Daytona](https://www.daytona.io)


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