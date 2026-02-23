"""
Skill registry: progressive disclosure for the model.
The model sees clean API definitions, not implementation details.
"""

SKILLS = {
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
}


def list_skills():
    """Return list of {name, description} for all skills."""
    return [{"name": name, "description": s["description"]} for name, s in SKILLS.items()]


def get_skill_schema(name):
    """Return schema for a skill (name, description, python_api, usage) or None."""
    skill = SKILLS.get(name)
    if not skill:
        return None
    return {
        "name": name,
        "description": skill["description"],
        "python_api": skill["python_api"],
        "usage": "Call tool " + name + " with the parameters described above.",
    }
