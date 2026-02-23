"""Daytona sandbox: create, sync workspace, run code in isolation, destroy. Local fallback when Daytona is disabled."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Any

_sandbox: Optional[Any] = None
_daytona: Optional[Any] = None
_work_dir: Optional[str] = None

# Daytona SDK uses type union syntax (X | Y) that requires Python 3.10+
_PYTHON_MIN_DAYTONA = (3, 10)


def _get_daytona(api_key: str):
    if sys.version_info < _PYTHON_MIN_DAYTONA:
        raise RuntimeError(
            "Daytona sandbox requires Python 3.10 or newer (you have {}.{}). "
            "Use a newer Python or run without DAYTONA_API_KEY.".format(
                sys.version_info.major, sys.version_info.minor
            )
        )
    try:
        from daytona import Daytona, DaytonaConfig
    except ImportError:
        raise ImportError(
            "Daytona SDK not installed. Install with: pip install daytona"
        )
    config = DaytonaConfig(api_key=api_key)
    return Daytona(config)


def init_sandbox(api_key: str, workspace_root: str) -> Optional[Any]:
    """Create a Daytona sandbox and optionally sync workspace files. Returns sandbox or None on failure."""
    global _sandbox, _daytona, _work_dir
    if not api_key or not api_key.strip():
        return None
    try:
        _daytona = _get_daytona(api_key.strip())
        _sandbox = _daytona.create()
        _work_dir = _sandbox.get_work_dir()
        _sync_workspace_to_sandbox(workspace_root)
        return _sandbox
    except Exception as e:
        _sandbox = None
        _daytona = None
        _work_dir = None
        raise RuntimeError(f"Daytona sandbox init failed: {e}") from e


def _sync_workspace_to_sandbox(workspace_root: str) -> None:
    """Upload workspace directory into sandbox (under workspace/)."""
    if _sandbox is None:
        return
    root = Path(workspace_root)
    if not root.is_dir():
        return
    created_dirs = set()
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root)
            remote = os.path.join("workspace", str(rel))
            # Ensure parent chain exists (workspace, workspace/a, workspace/a/b, ...)
            parts = Path(remote).parts[:-1]
            for i in range(1, len(parts) + 1):
                parent = os.path.join(*parts[:i])
                if parent not in created_dirs:
                    try:
                        _sandbox.fs.create_folder(parent, "755")
                        created_dirs.add(parent)
                    except Exception:
                        pass
            try:
                _sandbox.fs.upload_file(str(path), remote)
            except Exception:
                pass


def destroy_sandbox() -> None:
    """Destroy the current sandbox and clear state."""
    global _sandbox, _daytona, _work_dir
    if _sandbox is not None and _daytona is not None:
        try:
            _daytona.delete(_sandbox)
        except Exception:
            pass
    _sandbox = None
    _daytona = None
    _work_dir = None


def get_sandbox() -> Optional[Any]:
    return _sandbox


def run_code_local(workspace_root: str, code: str, timeout: int = 15) -> str:
    """Execute Python code locally with workspace on path (skills importable). Fallback when no Daytona sandbox."""
    preamble = "import sys\nsys.path.insert(0, %r)\n" % (os.path.abspath(workspace_root),)
    full_code = preamble + code
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(full_code)
            path = f.name
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workspace_root,
        )
        os.unlink(path)
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        if result.returncode != 0:
            return f"[exit {result.returncode}]\n{err}\n{out}".strip()
        return out or "(no output)"
    except subprocess.TimeoutExpired:
        return "[error] Code run timed out."
    except Exception as e:
        return f"[error] {e}"


def run_code_in_sandbox(code: str, timeout: Optional[int] = 30) -> str:
    """Execute Python code in the Daytona sandbox. Returns stdout or error message."""
    if _sandbox is None:
        return "[error] No sandbox (Daytona not initialized or init failed)."
    # Ensure workspace is on path so "from skills import products" works
    preamble = "import sys\nsys.path.insert(0, 'workspace')\n"
    try:
        resp = _sandbox.process.code_run(preamble + code, timeout=timeout)
        out = (resp.artifacts and getattr(resp.artifacts, "stdout", None)) or resp.result or ""
        exit_code = getattr(resp, "exit_code", -1)
        if exit_code != 0:
            return f"[exit {exit_code}]\n{out}"
        return out.strip() or "(no output)"
    except Exception as e:
        return f"[error] {e}"


def download_file(remote_path: str) -> str:
    """Download a file from the sandbox. Path relative to sandbox work dir (e.g. result.txt or workspace/out.txt)."""
    if _sandbox is None:
        return "[error] No sandbox."
    path = remote_path.lstrip("/").replace("\\", "/")
    try:
        data = _sandbox.fs.download_file(path)
        return data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
    except Exception as e:
        return f"Error reading {remote_path}: {e}"


def exec_command(command: str, cwd: Optional[str] = None) -> str:
    """Run a shell command in the sandbox. Returns combined stdout or error."""
    if _sandbox is None:
        return "[error] No sandbox."
    try:
        resp = _sandbox.process.exec(command, cwd=cwd or _work_dir)
        out = (resp.artifacts and getattr(resp.artifacts, "stdout", None)) or getattr(resp, "result", "") or "(no output)"
        exit_code = getattr(resp, "exit_code", -1)
        return f"[exit {exit_code}]\n{out}".strip()
    except Exception as e:
        return f"[error] {e}"
