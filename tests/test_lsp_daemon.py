import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from langtools_mcp.langtools_daemon import ruff_runner


# Unit test the downloader to ensure it would download, extract, and chmod
@patch("langtools_mcp.langtools_daemon.ruff_runner.urllib.request.urlretrieve")
@patch("langtools_mcp.langtools_daemon.ruff_runner.tarfile.open")
def test_ensure_ruff_download_extract(mock_taropen, mock_urlretrieve, tmp_path):
    # Remove binary if exists
    ruff_bin = ruff_runner.RUFF_BIN
    if os.path.exists(ruff_bin):
        os.remove(ruff_bin)

    # Mock tarfile extraction to place an executable
    class DummyMember:
        name = "ruff"

    class DummyTar:
        def getmembers(self):
            return [DummyMember()]

        def extract(self, member, path):
            with open(os.path.join(path, member.name), "w") as f:
                f.write("")

    mock_taropen.return_value.__enter__.return_value = DummyTar()
    mock_urlretrieve.return_value = ("archive.tar.gz", None)
    bin_path, err = ruff_runner.ensure_ruff()
    assert bin_path.endswith("ruff")
    assert err is None
    assert os.access(bin_path, os.X_OK)


@patch("langtools_mcp.langtools_daemon.ruff_runner.subprocess.run")
def test_run_ruff_analysis_ok(mock_run, tmp_path):
    tf = tmp_path / "sample.py"
    tf.write_text("import os\n")
    proc_mock = MagicMock()
    proc_mock.returncode = 1
    proc_mock.stdout = json.dumps([{"code": "F401", "message": "unused import"}])
    proc_mock.stderr = ""
    mock_run.return_value = proc_mock
    result = ruff_runner.run_ruff_analysis(str(ruff_runner.RUFF_BIN), str(tf))
    assert result["status"] == "ok"
    output = json.loads(result["output"])
    assert output[0]["code"] == "F401"


@patch("langtools_mcp.langtools_daemon.ruff_runner.subprocess.run")
def test_run_ruff_analysis_fail(mock_run, tmp_path):
    tf = tmp_path / "sample.py"
    tf.write_text("import fail\n")
    proc_mock = MagicMock()
    proc_mock.returncode = 2
    proc_mock.stdout = ""
    proc_mock.stderr = "error"
    mock_run.return_value = proc_mock
    result = ruff_runner.run_ruff_analysis(str(ruff_runner.RUFF_BIN), str(tf))
    assert result["status"] == "fail"
    assert result["stderr"] == "error"
