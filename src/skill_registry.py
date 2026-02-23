"""
Skill registry: progressive disclosure for the model.
Built-in skills (fs_read, fs_write) plus dynamic skills from workspace/skills/*.py.
Each skill file in skills/ must define SKILL_DESCRIPTION and SKILL_PYTHON_API for agents.
"""

import os
import importlib.util
from typing import Dict, Any, Optional

# Built-in skills (always available)
BUILTIN_SKILLS: Dict[str, Dict[str, str]] = {
    "fs_read": {
        "description": "List directory or read file from workspace (path relative to workspace root)",
        "python_api": """
# Tool: fs_read
# List root: path "."
# Read file: path "filename" or "dir/file"
# Optional: lines "10" or "10-50" for a line range
fs_read(path: str, lines: str | None = None) -> JSON
""".strip(),
    },
    "fs_write": {
        "description": "Write or overwrite a text file in the workspace",
        "python_api": """
# Tool: fs_write
# Creates or overwrites file at path (relative to workspace root). Parent dirs created if needed.
fs_write(path: str, content: str) -> JSON
""".strip(),
    },
    "execute_code": {
        "description": "Execute Python in the sandbox. Import dynamic skills (from skills.<name> import ...). Use print() for output; use open() to write files, then read_output(path) to read them.",
        "python_api": """
# Tool: execute_code
# Run Python in the sandbox. Workspace and skills dir are on path. Use print() for stdout; use open() to write files, then read_output(path) to read them.
execute_code(code: str) -> JSON (stdout and stderr)
""".strip(),
    },
}


def _load_skills_from_dir(workspace_root: str) -> Dict[str, Dict[str, str]]:
    """Load skills from workspace_root/skills/*.py. Each module must define SKILL_DESCRIPTION and SKILL_PYTHON_API."""
    skills: Dict[str, Dict[str, str]] = {}
    skills_dir = os.path.join(workspace_root, "skills")
    if not os.path.isdir(skills_dir):
        return skills
    for name in sorted(os.listdir(skills_dir)):
        if name.startswith("_") or not name.endswith(".py"):
            continue
        mod_name = name[:-3]
        path = os.path.join(skills_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                "skill_registry._skill_" + mod_name, path
            )
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            desc = getattr(mod, "SKILL_DESCRIPTION", None)
            api = getattr(mod, "SKILL_PYTHON_API", None)
            if desc and api:
                skills[mod_name] = {"description": desc, "python_api": api.strip()}
        except Exception:
            continue
    return skills


def get_skills(workspace_root: str) -> Dict[str, Dict[str, str]]:
    """Return merged built-in and dynamically loaded skills. workspace_root used to find skills/ subdir."""
    out = dict(BUILTIN_SKILLS)
    out.update(_load_skills_from_dir(workspace_root))
    return out


def list_skills(workspace_root: Optional[str] = None) -> list:
    """Return list of {name, description} for all skills. Pass workspace_root to include skills/ subdir."""
    root = workspace_root or ""
    skills = get_skills(root) if root else BUILTIN_SKILLS
    return [{"name": name, "description": s["description"]} for name, s in skills.items()]


def get_skill_schema(name: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Return schema for a skill (name, description, python_api, usage) or None. Pass workspace_root to resolve dynamic skills."""
    root = workspace_root or ""
    skills = get_skills(root) if root else BUILTIN_SKILLS
    skill = skills.get(name)
    if not skill:
        return None
    return {
        "name": name,
        "description": skill["description"],
        "python_api": skill["python_api"],
        "usage": "Call tool " + name + " with the parameters described above."
        if name in BUILTIN_SKILLS
        else "Use in execute_code: from skills." + name + " import ...",
    }
