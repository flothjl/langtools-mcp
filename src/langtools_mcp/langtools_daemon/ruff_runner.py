import os
import shutil
import subprocess


def ensure_ruff():
    # Look for ruff in environment PATH (installed via pip/uvx)
    bin_path = shutil.which("ruff")
    if bin_path and os.access(bin_path, os.X_OK):
        return bin_path, None
    return None, (
        "Could not find 'ruff'. Ensure it's installed in your environment (pip install ruff / uvx)."
    )


def run_ruff_analysis(ruff_bin, file_path):
    try:
        cmd = [ruff_bin, "check", file_path, "--output-format=json"]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=False,
        )
        if proc.returncode == 0 or proc.returncode == 1:
            return {"status": "ok", "output": proc.stdout, "stderr": proc.stderr}
        return {
            "status": "fail",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exitcode": proc.returncode,
        }
    except Exception as e:
        return {"status": "fail", "error": str(e)}
