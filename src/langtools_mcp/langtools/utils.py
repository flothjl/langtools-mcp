import os
from pathlib import Path


def find_virtual_env(path: str) -> str | None:
    """
    Finds a virtual environment directory within the project root.
    Searches for common names like '.venv', 'venv', 'env'.
    """
    common_names = [".venv", "venv", "env", ".env"]
    for name in common_names:
        venv_path = Path(path) / name
        # Check for the activation script or python executable to confirm it's a venv
        if (venv_path / "bin" / "activate").exists() or (
            venv_path / "Scripts" / "activate.bat"
        ).exists():
            return str(venv_path)
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
