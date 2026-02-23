"""Load config from config.yaml with env overrides for API keys."""

import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _ROOT / "config.yaml"
_CONFIG_EXAMPLE = _ROOT / "config.example.yaml"


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    if yaml is None:
        raise ImportError("PyYAML required: pip install pyyaml")
    with open(path) as f:
        return yaml.safe_load(f) or {}


def get_config() -> dict:
    """Load config from config.yaml, with env overrides for secrets."""
    raw = _load_yaml(_CONFIG_PATH)
    if not raw and _CONFIG_EXAMPLE.exists():
        raw = _load_yaml(_CONFIG_EXAMPLE)

    openai_cfg = raw.get("openai") or {}
    daytona_cfg = raw.get("daytona") or {}
    workspace_cfg = raw.get("workspace") or {}
    agentfs_cfg = raw.get("agentfs") or {}

    api_key = os.environ.get("OPENAI_API_KEY") or openai_cfg.get("api_key") or ""
    daytona_key = os.environ.get("DAYTONA_API_KEY") or daytona_cfg.get("api_key") or ""

    workspace_root = workspace_cfg.get("root", "./workspace")
    if not os.path.isabs(workspace_root):
        workspace_root = str(_ROOT / workspace_root)

    agentfs_enabled = bool(agentfs_cfg.get("enabled", False))
    agentfs_id = (agentfs_cfg.get("id") or os.environ.get("AGENTFS_ID") or "ai-vfs-agent").strip()

    return {
        "openai_api_key": api_key,
        "openai_model": openai_cfg.get("model", "gpt-4o-mini"),
        "daytona_api_key": daytona_key,
        "workspace_root": workspace_root,
        "max_iterations": raw.get("max_iterations", 10),
        "timeout_seconds": float(raw.get("timeout_seconds", 5.0)),
        "agentfs_enabled": agentfs_enabled,
        "agentfs_id": agentfs_id,
    }
