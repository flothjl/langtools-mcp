import json
import tempfile

from langtools_mcp.langtools.ruff_analyzer import RuffAnalyzer

# Test RuffAnalyzer with mocked daemon client


def test_ruff_analyzer_clean(monkeypatch):
    resp = {"status": "ok", "output": json.dumps([]), "stderr": ""}
    monkeypatch.setattr(
        "langtools_mcp.langtools.langtools_daemon_client.LangtoolsDaemonClient.analyze",
        lambda self, f, l: resp,
    )
    analyzer = RuffAnalyzer()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tf:
        result = analyzer.analyze(tf.name)
    assert result["status"] == "ok"
    assert json.loads(result["output"]) == []


def test_ruff_analyzer_with_issues(monkeypatch):
    issues = [{"message": "F401: unused import", "code": "F401", "fix": False}]
    resp = {"status": "ok", "output": json.dumps(issues), "stderr": ""}
    monkeypatch.setattr(
        "langtools_mcp.langtools.langtools_daemon_client.LangtoolsDaemonClient.analyze",
        lambda self, f, l: resp,
    )
    analyzer = RuffAnalyzer()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tf:
        result = analyzer.analyze(tf.name)
    assert result["status"] == "ok"
    assert len(json.loads(result["output"])) == 1
    assert json.loads(result["output"])[0]["code"] == "F401"


# Errors from daemon are passed through
def test_ruff_analyzer_error(monkeypatch):
    err_resp = {"status": "fail", "stderr": "crashed"}
    monkeypatch.setattr(
        "langtools_mcp.langtools.langtools_daemon_client.LangtoolsDaemonClient.analyze",
        lambda self, f, l: err_resp,
    )
    analyzer = RuffAnalyzer()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tf:
        result = analyzer.analyze(tf.name)
    assert result["status"] == "fail"
    assert result["stderr"] == "crashed"
