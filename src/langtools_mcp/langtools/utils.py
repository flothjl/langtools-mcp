import os
from collections import deque
from pathlib import Path
from typing import Iterable, Optional


class NoRootFoundException(Exception): ...


def search_down_for_roots(
    root_path: str,
    targets: Iterable[str],
    max_depth: int = 5,
    ignore: Iterable[str] = (),
) -> list[str]:
    """
    Recursively search downward from root_path for directories containing any of the target files/dirs.
    Skips directories or files in `ignore`.
    Returns a list of matching directory paths.
    """

    root = Path(root_path).resolve()
    found = []
    queue = deque([(root, 0)])
    ignore_set = set(ignore)

    while queue:
        curr, depth = queue.popleft()
        if depth > max_depth:
            continue
        # Ignore current directory if in ignore list
        if curr.name in ignore_set:
            continue
        # Check for targets in current directory
        for target in targets:
            if (curr / target).exists():
                found.append(str(curr))
                break
        # Queue subdirs, skipping those in ignore set
        for child in curr.iterdir():
            if (
                child.is_dir()
                and child.name not in ignore_set
                and not child.name.startswith(".")
            ):
                queue.append((child, depth + 1))
    if len(found) == 0:
        raise NoRootFoundException(f"No root found for the targets provided: {targets}")
    return found


def search_down_for_root(
    root_path: str,
    targets: Iterable[str],
    max_depth: int = 5,
    ignore: Iterable[str] = (),
) -> str:
    out = search_down_for_roots(root_path, targets, max_depth, ignore)
    return out[0]


def find_ts_root(path: str):
    return search_down_for_root(
        path,
        {"tsconfig.json", "package.json", "jsconfig.json"},
        ignore={"node_modules"},
    )


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
