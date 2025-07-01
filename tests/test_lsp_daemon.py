import pytest
from unittest.mock import patch, MagicMock
from langtools_mcp.langtools_daemon import ruff_runner

@patch("subprocess.run")
def test_run_ruff_analysis_ok(mock_run, tmp_path):
    tf = tmp_path / "sample.py"
    tf.write_text("import os\n")
    proc_mock = MagicMock()
    proc_mock.returncode = 1
    proc_mock.stdout = '[{"code": "F401", "message": "unused import"}]'
    proc_mock.stderr = ""
    mock_run.return_value = proc_mock
    result = ruff_runner.run_ruff_analysis("ruff", str(tf))
    assert result["status"] == "ok"
    output = result["output"]
    assert "F401" in output

@patch("subprocess.run")
def test_run_ruff_analysis_fail(mock_run, tmp_path):
    tf = tmp_path / "sample.py"
    tf.write_text("import fail\n")
    proc_mock = MagicMock()
    proc_mock.returncode = 2
    proc_mock.stdout = ""
    proc_mock.stderr = "error"
    mock_run.return_value = proc_mock
    result = ruff_runner.run_ruff_analysis("ruff", str(tf))
    assert result["status"] == "fail"
    assert result["stderr"] == "error"
