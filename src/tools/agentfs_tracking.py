"""Optional AgentFS integration: record tool calls for audit and stats. No-op if agentfs-sdk not installed."""

import asyncio
import json
from typing import Any


def track_tool_call(agentfs_id: str, name: str, arguments: dict, result: str) -> None:
    """Record a tool call to AgentFS (async SDK). No-op if agentfs_sdk not installed or id empty."""
    if not (agentfs_id and agentfs_id.strip()):
        return

    async def _record() -> None:
        try:
            from agentfs_sdk import AgentFS, AgentFSOptions
        except ImportError:
            return
        agent = None
        try:
            agent = await AgentFS.open(AgentFSOptions(id=agentfs_id.strip()))
            call_id = await agent.tools.start(name, arguments)
            # Store result (truncate if huge to avoid blowing the DB)
            payload: Any = result
            if len(result) > 50_000:
                payload = result[:50_000] + "\n...[truncated]"
            try:
                payload = json.loads(result) if result.strip().startswith("{") else payload
            except (json.JSONDecodeError, TypeError):
                pass
            await agent.tools.success(call_id, payload)
        except Exception:
            pass
        finally:
            if agent is not None:
                await agent.close()

    try:
        asyncio.run(_record())
    except Exception:
        pass
