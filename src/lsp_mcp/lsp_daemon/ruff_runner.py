import os

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "tools")
RUFF_FILENAME = "ruff"
RUFF_BIN = os.path.join(TOOLS_DIR, RUFF_FILENAME)

def ensure_ruff():
    if os.path.exists(RUFF_BIN) and os.access(RUFF_BIN, os.X_OK):
        return RUFF_BIN, None
    return None, (
        f"Ruff binary not found or not executable at {RUFF_BIN}. "
        "Please manually download the correct version for your system/platform "
        "and place it in this directory, with executable permissions."
    )

def run_ruff_analysis(ruff_bin, file_path):
    import subprocess
    import json
    try:
        cmd = [ruff_bin, "check", file_path, "--output-format=json"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", check=False)
        if proc.returncode == 0 or proc.returncode == 1:
            return {"status": "ok", "output": proc.stdout, "stderr": proc.stderr}
        return {"status": "fail", "stdout": proc.stdout, "stderr": proc.stderr, "exitcode": proc.returncode}
    except Exception as e:
        return {"status": "fail", "error": str(e)}
