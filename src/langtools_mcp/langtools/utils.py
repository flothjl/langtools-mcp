import os
from pathlib import Path


def find_virtual_env(path: str, max_depth=4) -> str | None:
    """
    Recursively search downward from `path` (up to max_depth levels)
    for a virtual environment directory.
    Looks for typical names and activation files.
    """
    root = Path(path)
    candidate_names = {".venv", "venv", "env", ".env"}
    # Breadth-first search up to max_depth
    queue = [(root, 0)]
    while queue:
        curr, depth = queue.pop(0)
        if depth > max_depth:
            continue
        for child in curr.iterdir():
            if child.is_dir() and child.name in candidate_names:
                # Check for venv activation script (Unix or Windows)
                if (child / "bin" / "activate").exists() or (
                    child / "Scripts" / "activate.bat"
                ).exists():
                    return str(child)
            # Enqueue subdirectories to search further down
            if child.is_dir() and not child.name.startswith("."):
                queue.append((child, depth + 1))
    return None


def find_go_module_root(path: str) -> str:
    path = os.path.abspath(path)

    # If it's a file, get its containing directory
    if os.path.isfile(path):
        dir_path = os.path.dirname(path)
    else:
        dir_path = path

    while True:
        maybe_mod = os.path.join(dir_path, "go.mod")
        if os.path.isfile(maybe_mod):
            return dir_path
        parent = os.path.dirname(dir_path)
        if parent == dir_path:
            break  # Reached the filesystem root
        dir_path = parent

    # Fallback: return starting directory (normalized)
    return os.path.abspath(path)
