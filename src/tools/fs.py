"""fs_read tool: list directory or read file from workspace."""

import json
from pathlib import Path

FS_READ_SCHEMA = {
    "description": "Read a file or list a directory in the workspace. Use path '.' to list root; use path 'filename' or 'dir/file' to read or list.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path from workspace root (e.g. '.' or 'src/main.py')",
            },
            "lines": {
                "type": "string",
                "description": "Optional line range: '10' or '10-50'",
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    },
}


def _resolve(workspace_root: str, path: str) -> Path:
    """Resolve path inside workspace; disallow escape."""
    root = Path(workspace_root).resolve()
    path = path.strip().lstrip("/")
    if not path or path == ".":
        return root
    full = (root / path).resolve()
    if not str(full).startswith(str(root)):
        raise PermissionError("Path escapes workspace")
    return full


def _read_lines(content: str, lines_spec: str) -> str:
    """Return content for line range 'N' or 'N-M' (1-based inclusive)."""
    lines = content.splitlines()
    total = len(lines)
    if "-" in lines_spec:
        a, b = lines_spec.strip().split("-", 1)
        start = max(1, int(a.strip()))
        end = min(total, int(b.strip()))
    else:
        start = end = max(1, min(total, int(lines_spec.strip())))
    start = max(1, min(start, total))
    end = max(start, min(end, total))
    selected = lines[start - 1 : end]
    return "\n".join(f"{i}|{line}" for i, line in enumerate(selected, start=start))


def execute_fs_read(
    path: str,
    workspace_root: str,
    lines: str | None = None,
) -> str:
    """List directory or read file; returns JSON string for the agent."""

    try:
        full = _resolve(workspace_root, path)
    except Exception as e:
        return json.dumps({"success": False, "path": path, "error": str(e)})

    if not full.exists():
        return json.dumps({"success": False, "path": path, "error": "NOT_FOUND"})

    if full.is_dir():
        entries = []
        try:
            for e in sorted(full.iterdir()):
                rel = e.relative_to(Path(workspace_root).resolve())
                kind = "directory" if e.is_dir() else "file"
                entries.append({"path": str(rel), "kind": kind})
        except OSError as err:
            return json.dumps({"success": False, "path": path, "error": str(err)})
        return json.dumps({
            "success": True,
            "path": path,
            "type": "directory",
            "entries": entries,
        })

    # file
    try:
        raw = full.read_text(encoding="utf-8", errors="replace")
    except OSError as err:
        return json.dumps({"success": False, "path": path, "error": str(err)})

    truncated = False
    if lines:
        try:
            text = _read_lines(raw, lines)
        except (ValueError, TypeError):
            text = raw
    else:
        line_count = raw.count("\n") + (1 if raw else 0)
        if line_count > 200:
            text = _read_lines(raw, "1-200")
            truncated = True
        else:
            text = "\n".join(f"{i}|{line}" for i, line in enumerate(raw.splitlines(), start=1))

    return json.dumps({
        "success": True,
        "path": path,
        "type": "file",
        "content": text,
        "truncated": truncated,
    })
