import os
import sys
import shutil
import tempfile
import urllib.request
import tarfile
import subprocess
import platform
import stat

def ruff_url():
    # Only supporting Apple Silicon for v0 (darwin_arm64)
    VERSION = "0.4.7"  # or latest stable; could be dynamic
    return f"https://github.com/astral-sh/ruff/releases/download/v{VERSION}/ruff-v{VERSION}-arm64-apple-darwin.tar.gz"

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "tools")
RUFF_FILENAME = "ruff"
RUFF_BIN = os.path.join(TOOLS_DIR, RUFF_FILENAME)

def ensure_ruff():
    if os.path.exists(RUFF_BIN) and os.access(RUFF_BIN, os.X_OK):
        return RUFF_BIN, None
    os.makedirs(TOOLS_DIR, exist_ok=True)
    url = ruff_url()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            archive = os.path.join(tmpdir, "ruff.tar.gz")
            urllib.request.urlretrieve(url, archive)
            with tarfile.open(archive) as tar:
                for member in tar.getmembers():
                    if member.name.endswith("/ruff") or member.name == "ruff":
                        member.name = os.path.basename(member.name)
                        tar.extract(member, TOOLS_DIR)
                        bin_path = os.path.join(TOOLS_DIR, member.name)
                        os.chmod(bin_path, os.stat(bin_path).st_mode | stat.S_IXUSR)
                        shutil.move(bin_path, RUFF_BIN)
                        break
        if os.access(RUFF_BIN, os.X_OK):
            return RUFF_BIN, None
        else:
            return None, "Downloaded ruff is not executable"
    except Exception as e:
        return None, str(e)

def run_ruff_analysis(ruff_bin, file_path):
    cmd = [ruff_bin, "check", file_path, "--output-format=json"]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", check=False)
        if proc.returncode == 0 or proc.returncode == 1:
            # Ruff: 0 for clean, 1 for warnings/errors
            return {"status": "ok", "output": proc.stdout, "stderr": proc.stderr}
        return {"status": "fail", "stdout": proc.stdout, "stderr": proc.stderr, "exitcode": proc.returncode}
    except Exception as e:
        return {"status": "fail", "error": str(e)}
