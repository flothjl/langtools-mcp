import tempfile
import pytest
from unittest.mock import patch, MagicMock
import json

from lsp_mcp.lsp.pyright_analyzer import PyrightAnalyzer

def make_mock_subprocess(stdout_json, returncode=0, stderr=''):
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout_json
    mock.stderr = stderr
    return mock

def test_pyright_no_issues():
    analyzer = PyrightAnalyzer()
    json_out = json.dumps({'generalDiagnostics': []})
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tf:
        with patch("subprocess.run", return_value=make_mock_subprocess(json_out)):
            result = analyzer.analyze(tf.name)
        assert result["summary"]["errors"] == 0
        assert result["summary"]["warnings"] == 0
        assert result["summary"]["deprecations"] == 0

def test_pyright_with_errors_and_deprecations():
    analyzer = PyrightAnalyzer()
    test_diag = [
        {"file": "x.py", "severity": "error", "message": "some error"},
        {"file": "x.py", "severity": "warning", "message": "deprecation warning"},
        {"file": "x.py", "severity": "warning", "message": "yikes"},
    ]
    json_out = json.dumps({'generalDiagnostics': test_diag})
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tf:
        tf_name = tf.name
        for d in test_diag:
            d["file"] = tf_name
        with patch("subprocess.run", return_value=make_mock_subprocess(json.dumps({'generalDiagnostics': test_diag}))):
            result = analyzer.analyze(tf_name)
        assert result["summary"]["errors"] == 1
        assert result["summary"]["warnings"] == 2
        assert result["summary"]["deprecations"] == 1
        assert len(result["deprecations"]) == 1

def test_pyright_not_installed():
    analyzer = PyrightAnalyzer()
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tf:
        with patch("subprocess.run", return_value=make_mock_subprocess('', 127, 'pyright: command not found')):
            result = analyzer.analyze(tf.name)
        assert "not installed" in result["error"]

def test_pyright_bad_json():
    analyzer = PyrightAnalyzer()
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tf:
        with patch("subprocess.run", return_value=make_mock_subprocess('!!!not json!!!', 0)):
            result = analyzer.analyze(tf.name)
        assert result["error"].startswith("pyright output could not be parsed")
