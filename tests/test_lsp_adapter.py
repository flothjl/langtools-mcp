import pytest
from unittest.mock import MagicMock, patch
from langtools_mcp.langtools_daemon.lsp_adapter import BasicLSPClient, BasicGoplsAdapter
import io
import json

class DummyPopen:
    def __init__(self, stdout_lines=None):
        self.stdin = io.BytesIO()
        self.stdout_lines = stdout_lines or []
        self.stdout_idx = 0
        self.stdout = self
        self.stderr = io.BytesIO()
        self.terminated = False
        self.returncode = 0
    def readline(self):
        if self.stdout_idx >= len(self.stdout_lines):
            return b''
        l = self.stdout_lines[self.stdout_idx]
        self.stdout_idx += 1
        return l
    def read(self, n):
        # Always return correct content for mock message
        return self.stdout_lines[self.stdout_idx-1][self.stdout_lines[self.stdout_idx-1].find(b'\r\n\r\n')+4:]
    def write(self, b):
        return len(b)
    def flush(self):
        return None
    def terminate(self):
        self.terminated = True
    def wait(self, timeout=None):
        return 0
    def kill(self):
        self.terminated = True

@patch("subprocess.Popen")
def test_lspclient_init_and_shutdown(mock_popen):
    mock_proc = DummyPopen()
    mock_popen.return_value = mock_proc
    client = BasicLSPClient(["/bin/foo"])
    client.start()
    client.shutdown()
    assert mock_proc.terminated

@patch("subprocess.Popen")
@patch("uuid.uuid4")
def test_send_request_response(mock_uuid4, mock_popen):
    fake_id = "fake-uuid"
    mock_uuid4.return_value = fake_id
    response = {
        "jsonrpc": "2.0",
        "id": fake_id,
        "result": {"foo": "bar"}
    }
    payload = json.dumps(response).encode("utf-8")
    lines = [f"Content-Length: {len(payload)}\r\n".encode("utf-8"),
             b"\r\n",
             payload]
    mock_proc = DummyPopen(stdout_lines=lines)
    mock_popen.return_value = mock_proc
    client = BasicLSPClient(["/bin/foo"])
    client.start()
    resp = client.send_request("initialize", {})
    assert resp == response
    client.shutdown()

@patch("subprocess.Popen")
@patch("uuid.uuid4")
def test_gopls_adapter_batch_diag(mock_uuid4, mock_popen, tmp_path):
    diag_method = "textDocument/publishDiagnostics"
    file_path = tmp_path / "foo.go"
    file_path.write_text("package main\nfunc main(){}\n")
    msg = {"jsonrpc": "2.0", "method": diag_method, "params": {"uri": f"file://{file_path}", "diagnostics": []}}
    payload = json.dumps(msg).encode("utf-8")
    lines = [b"Content-Length: 47\r\n", b"\r\n", payload]
    mock_proc = DummyPopen(stdout_lines=lines)
    mock_popen.return_value = mock_proc
    mock_uuid4.return_value = "test-id"
    adapter = BasicGoplsAdapter(gopls_path="gopls")
    result = adapter.analyze(str(file_path))
    assert result["status"] == "ok"
    if "diagnostics" in result:
        assert isinstance(result["diagnostics"], list)
    elif "note" in result:
        assert result["note"].startswith("No diagnostics")
    else:
        assert False, "Result missing diagnostics/note"
    adapter.lsp.shutdown()
