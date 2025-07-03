import tempfile
from unittest.mock import MagicMock, patch

import pytest

from langtools_mcp.langtools_daemon.gopls_lsp_adapter import GoplsLSPAdapter
from langtools_mcp.langtools_daemon.lsp_pool import LSPServerPool


class DummyLSPAdapter:
    def __init__(self, root_path, **kwargs):
        self.root_path = root_path
        self.shut_down = False
        self.analyze_called = 0

    def analyze(self, file_path):
        self.analyze_called += 1
        return {"status": "ok", "root": self.root_path, "file": file_path}

    def shutdown(self):
        self.shut_down = True


@patch("langtools_mcp.langtools_daemon.gopls_lsp_adapter.BasicLSPClient")
def test_lsp_pool_singleton_adapter(mock_lsp_client):
    pool = LSPServerPool({"go": DummyLSPAdapter})
    adapter1 = pool.get_server("go", "/foo/project1")
    adapter2 = pool.get_server("go", "/foo/project1")
    adapter3 = pool.get_server("go", "/foo/project2")
    assert adapter1 is adapter2
    assert adapter1 is not adapter3
    assert adapter2.root_path == "/foo/project1"
    assert adapter3.root_path == "/foo/project2"

    pool.shutdown()
    assert adapter1.shut_down
    assert adapter3.shut_down


@patch("langtools_mcp.langtools_daemon.gopls_lsp_adapter.BasicLSPClient")
def test_gopls_lsp_adapter_persistence(mock_lsp_client, tmp_path):
    # Simulate persistent server (should not re-init for multiple analyzes)
    fake_proc = MagicMock()
    fake_proc.stdout.readline.return_value = b""
    mock_lsp_client.return_value = fake_proc

    root = tmp_path
    adapter = GoplsLSPAdapter(root_path=str(root), gopls_path="gopls")
    adapter.lsp = MagicMock()
    adapter.lsp.send_notification.return_value = None
    adapter.lsp.gather_notifications.return_value = [{"dummy": 1}]
    adapter.started = False

    with tempfile.NamedTemporaryFile(suffix=".go") as tf:
        tf.write(b"package main\nfunc main(){}")
        tf.flush()
        result1 = adapter.analyze(tf.name)
        assert result1["status"] == "ok"
        adapter.lsp.gather_notifications.return_value = [{"dummy": 2}]
        result2 = adapter.analyze(tf.name)
        assert result2["status"] == "ok"
    adapter.shutdown()
