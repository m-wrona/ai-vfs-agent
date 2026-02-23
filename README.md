# ai-vfs-agent

An LLM agent that uses a **virtual workspace filesystem** (read/write via `fs_read`/`fs_write`) and an optional **sandbox** (Daytona) to run code. 
The agent discovers **built-in and dynamic skills** (`list_skills` / `get_skill`); domain skills (e.g. products, orders) live in `workspace/skills/*.py` and are used inside the sandbox via `execute_code`. 
Each turn returns a **Plan** (what it did and which skills it used) and a **Result** (the answer or a clear failure message).


Tools:

* [AgentFS](https://www.agentfs.ai) — when enabled in config (`agentfs.enabled: true` and optional `agentfs.id`), every tool call (fs_read, fs_write, list_skills, get_skill, execute_code, etc.) is recorded to an AgentFS SQLite store (`.agentfs/{id}.db`) for audit and tool-call stats. Install `agentfs-sdk` and set `agentfs.enabled` in `config.yaml` to use it.
* [Daytona](https://www.daytona.io) — when configured (`DAYTONA_API_KEY`), the agent runs `execute_code` in an isolated cloud sandbox: the workspace is synced in, Python runs there (so skills and file access are confined), and you get `read_output` / `shell`. Without Daytona, code runs locally in a subprocess (same skills, no isolation).


```
User Prompt
     ↓
Agent Harness
     ↓
LLM (plan) <- Tool capabilities
     ↓
Plan execution Tool calls (i.e. fs_read)
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
   - `daytona.api_key` (or `DAYTONA_API_KEY`) — optional, for sandbox code execution  
   - `agentfs.enabled` and optional `agentfs.id` — optional, to record tool calls to AgentFS (requires `pip install agentfs-sdk`)  
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

## AgentFS - samples

```
sqlite> select * from tool_calls;
1|list_skills|{}|{"skills": [{"name": "fs_read", "description": "List directory or read file from workspace (path relative to workspace root)"}, {"name": "fs_write", "description": "Write or overwrite a text file in the workspace"}, {"name": "execute_code", "description": "Execute Python in the sandbox. Import dynamic skills (from skills.<name> import ...). Use print() for output; use open() to write files, then read_output(path) to read them."}, {"name": "orders", "description": "Order data linked to products via productId (id, productId, customerId, quantity, date, status)"}, {"name": "products", "description": "Product catalog with pricing and inventory data (id, name, price, category, stock)"}]}||success|1771883224|1771883224|0
2|get_skill|{"name": "products"}|{"name": "products", "description": "Product catalog with pricing and inventory data (id, name, price, category, stock)", "python_api": "# Module: skills.products (add to path: workspace)\nproducts: list[dict]  # id, name, price, category, stock\ndef get_product_by_id(id: str) -> dict | None\ndef get_products_by_category(category: str) -> list[dict]\ndef get_in_stock_products() -> list[dict]", "usage": "Use in execute_code: from skills.products import ..."}||success|1771883225|1771883225|0
3|get_skill|{"name": "orders"}|{"name": "orders", "description": "Order data linked to products via productId (id, productId, customerId, quantity, date, status)", "python_api": "# Module: skills.orders (add to path: workspace)\norders: list[dict]  # id, productId, customerId, quantity, date, status\ndef get_orders_by_product(product_id: str) -> list[dict]\ndef get_orders_by_customer(customer_id: str) -> list[dict]\ndef get_orders_by_status(status: str) -> list[dict]", "usage": "Use in execute_code: from skills.orders import ..."}||success|1771883225|1771883225|0
4|execute_code|{"code": "from skills.products import products, get_product_by_id\nfrom skills.orders import orders\n\nrevenue = {}\nfor o in orders:\n    p = get_product_by_id(o['productId'])\n    if p:\n        cat = p['category']\n        revenue[cat] = revenue.get(cat, 0) + p['price'] * o['quantity']\nprint(revenue)"}|"{'electronics': 1169.89, 'office': 604.9300000000001}"||success|1771883228|1771883228|0
sqlite>
```

## Docs

* [Solving a Million-Step LLM Task with Zero Errors](https://arxiv.org/abs/2511.09030)