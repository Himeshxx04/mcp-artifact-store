"""
Utility for reading Python source files from a directory.
No LLM, no MCP — just disk I/O used by the analyzer agent.
"""

from pathlib import Path

# Directories that are never worth analyzing
_SKIP_DIRS = {"__pycache__", "venv", ".venv", "versions", ".git", "node_modules", "dist", "build"}


def read_python_files(directory: str) -> dict[str, str]:
    """
    Walk a directory recursively and return all readable .py files.

    Returns:
        dict mapping relative_path -> file_content
        e.g. {"backend/services/storage.py": "from fastapi import ..."}

    Skips: __pycache__, venv, migrations/versions, .git
    """
    base = Path(directory).resolve()
    if not base.exists():
        raise FileNotFoundError(f"Directory not found: {base}")
    if not base.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {base}")

    files: dict[str, str] = {}

    for path in sorted(base.rglob("*.py")):
        # Skip any path that contains a blacklisted directory
        if any(skip in path.parts for skip in _SKIP_DIRS):
            continue
        try:
            content = path.read_text(encoding="utf-8")
            relative = str(path.relative_to(base))
            files[relative] = content
        except (OSError, UnicodeDecodeError):
            # Unreadable file — skip silently
            continue

    return files
