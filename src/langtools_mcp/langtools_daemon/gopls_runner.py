import os
import shutil


def ensure_gopls():
    bin_path = shutil.which("gopls")
    if bin_path and os.access(bin_path, os.X_OK):
        return bin_path, None
    return None, ("Could not find 'gopls'. Ensure golang is installed")


def run_gopls_analysis(gopls_bin, file_path):
    import subprocess

    try:
        cmd = [gopls_bin, "check", file_path]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=False,
        )
        return {
            "status": "ok" if proc.returncode == 0 else "fail",
            "output": proc.stdout,
            "stderr": proc.stderr,
            "exitcode": proc.returncode,
        }
    except Exception as e:
        return {"status": "fail", "error": str(e)}
