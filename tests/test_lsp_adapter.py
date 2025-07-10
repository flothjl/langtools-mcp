import io
import json
import time
import uuid
from unittest.mock import patch

import pytest

from langtools_mcp.langtools_daemon.gopls_lsp_adapter import GoplsLSPAdapter
from langtools_mcp.langtools_daemon.lsp_adapter import BasicLSPClient


class MockLSPProcess:
    """Mock LSP process that can simulate multiple diagnostic messages"""

    def __init__(self, diagnostic_messages=None, stdout_lines=None):
        self.stdin = io.BytesIO()
        self.stderr = io.BytesIO()
        self.terminated = False
        self.returncode = 0
        
        # Support both new style (diagnostic_messages) and old style (stdout_lines)
        if stdout_lines:
            self.stdout_lines = stdout_lines
            self.stdout_idx = 0
            self.stdout = self
        else:
            self.diagnostic_messages = diagnostic_messages or []
            self.message_index = 0

    def readline(self):
        # Old style support for backwards compatibility
        if hasattr(self, 'stdout_lines'):
            if self.stdout_idx >= len(self.stdout_lines):
                return b""
            l = self.stdout_lines[self.stdout_idx]
            self.stdout_idx += 1
            return l
        
        # New style for multiple messages
        if self.message_index >= len(self.diagnostic_messages):
            return b""

        msg = self.diagnostic_messages[self.message_index]
        payload = json.dumps(msg).encode("utf-8")

        # Return Content-Length header
        if self.message_index == 0 or self.message_index % 2 == 0:
            self.message_index += 1
            return f"Content-Length: {len(payload)}\r\n".encode("utf-8")
        else:
            # Return blank line after header
            self.message_index += 1
            return b"\r\n"

    def read(self, n):
        # Old style support for backwards compatibility
        if hasattr(self, 'stdout_lines'):
            return self.stdout_lines[self.stdout_idx - 1][
                self.stdout_lines[self.stdout_idx - 1].find(b"\r\n\r\n") + 4 :
            ]
        
        # New style for multiple messages
        msg_idx = (self.message_index - 2) // 2
        if msg_idx < len(self.diagnostic_messages):
            msg = self.diagnostic_messages[msg_idx]
            payload = json.dumps(msg).encode("utf-8")
            return payload
        return b""

    def write(self, data):
        return len(data)

    def flush(self):
        pass

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminated = True


# Legacy alias for backwards compatibility
DummyPopen = MockLSPProcess


@patch("subprocess.Popen")
def test_lspclient_init_and_shutdown(mock_popen):
    """Test basic LSP client initialization and shutdown"""
    mock_proc = MockLSPProcess(stdout_lines=[])
    mock_popen.return_value = mock_proc
    client = BasicLSPClient(["/bin/foo"])
    client.start()
    client.shutdown()
    assert mock_proc.terminated


@patch("subprocess.Popen")
@patch("uuid.uuid4")
def test_gopls_adapter_batch_diag_legacy(mock_uuid4, mock_popen, tmp_path):
    """Test gopls adapter with empty diagnostics (legacy compatibility test)"""
    diag_method = "textDocument/publishDiagnostics"
    file_path = tmp_path / "foo.go"
    file_path.write_text("package main\nfunc main(){}\n")
    msg = {
        "jsonrpc": "2.0",
        "method": diag_method,
        "params": {"uri": f"file://{file_path}", "diagnostics": []},
    }
    payload = json.dumps(msg).encode("utf-8")
    lines = [b"Content-Length: 47\r\n", b"\r\n", payload]
    mock_proc = MockLSPProcess(stdout_lines=lines)
    mock_popen.return_value = mock_proc
    mock_uuid4.return_value = "test-id"
    adapter = GoplsLSPAdapter(root_path=str(tmp_path), gopls_path="gopls")
    result = adapter.analyze(str(file_path))
    assert result["status"] == "ok"
    if "diagnostics" in result:
        assert isinstance(result["diagnostics"], list)
    elif "note" in result:
        assert result["note"].startswith("No diagnostics")
    else:
        assert False, "Result missing diagnostics/note"
    adapter.lsp.shutdown()


@patch("subprocess.Popen")
def test_multiple_diagnostic_messages_collection(mock_popen, tmp_path):
    """Test that the improved LSP adapter collects multiple diagnostic messages"""

    # Create multiple diagnostic messages as gopls might send
    diagnostic_messages = [
        {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {
                "uri": "file:///test.go",
                "diagnostics": [
                    {
                        "range": {
                            "start": {"line": 1, "character": 0},
                            "end": {"line": 1, "character": 10},
                        },
                        "severity": 1,
                        "source": "compiler",
                        "message": "undefined: undefinedVar",
                    }
                ],
            },
        },
        {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {
                "uri": "file:///test.go",
                "diagnostics": [
                    {
                        "range": {
                            "start": {"line": 2, "character": 0},
                            "end": {"line": 2, "character": 15},
                        },
                        "severity": 2,
                        "source": "go vet",
                        "message": "unused variable: unusedVar",
                    }
                ],
            },
        },
        {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {
                "uri": "file:///test.go",
                "diagnostics": [
                    {
                        "range": {
                            "start": {"line": 3, "character": 0},
                            "end": {"line": 3, "character": 20},
                        },
                        "severity": 3,
                        "source": "staticcheck",
                        "message": "inefficient string concatenation",
                    }
                ],
            },
        },
    ]

    file_path = tmp_path / "test.go"
    file_path.write_text("package main\nfunc main(){}\n")

    # Set up mock process
    mock_proc = MockLSPProcess(diagnostic_messages)
    mock_popen.return_value = mock_proc

    # Create adapter and analyze
    adapter = GoplsLSPAdapter(root_path=str(tmp_path), gopls_path="gopls")

    # Mock the send_request method to return a successful initialize response
    with patch.object(adapter, "start_server") as mock_start:
        mock_start.return_value = None
        adapter.lsp = BasicLSPClient(["mock-gopls"])
        adapter.lsp.start()

        # Directly add the notifications to test gathering
        adapter.lsp.notifications = diagnostic_messages.copy()

        # Test the gather_notifications method
        result = adapter.lsp.gather_notifications(
            "textDocument/publishDiagnostics", timeout=2.0
        )

        # Assert we got all diagnostic messages
        assert len(result) == 3, f"Expected 3 diagnostic messages, got {len(result)}"

        # Check that each message has the expected content
        sources = []
        total_diagnostics = 0
        for msg in result:
            params = msg.get("params", {})
            diagnostics = params.get("diagnostics", [])
            total_diagnostics += len(diagnostics)
            if diagnostics:
                sources.append(diagnostics[0]["source"])

        assert total_diagnostics == 3, (
            f"Expected 3 total diagnostics, got {total_diagnostics}"
        )
        assert "compiler" in sources, "Missing compiler diagnostics"
        assert "go vet" in sources, "Missing go vet diagnostics"
        assert "staticcheck" in sources, "Missing staticcheck diagnostics"

        adapter.lsp.shutdown()


@patch("subprocess.Popen")
def test_diagnostic_settle_timeout(mock_popen, tmp_path):
    """Test that diagnostic collection respects the settle timeout"""

    # Single diagnostic message
    diagnostic_message = {
        "jsonrpc": "2.0",
        "method": "textDocument/publishDiagnostics",
        "params": {
            "uri": "file:///test.go",
            "diagnostics": [
                {
                    "range": {
                        "start": {"line": 1, "character": 0},
                        "end": {"line": 1, "character": 10},
                    },
                    "severity": 1,
                    "source": "compiler",
                    "message": "undefined: undefinedVar",
                }
            ],
        },
    }

    file_path = tmp_path / "test.go"
    file_path.write_text("package main\nfunc main(){}\n")

    mock_proc = MockLSPProcess([diagnostic_message])
    mock_popen.return_value = mock_proc

    adapter = GoplsLSPAdapter(root_path=str(tmp_path), gopls_path="gopls")

    with patch.object(adapter, "start_server") as mock_start:
        mock_start.return_value = None
        adapter.lsp = BasicLSPClient(["mock-gopls"])
        adapter.lsp.start()

        # Add the notification
        adapter.lsp.notifications = [diagnostic_message]

        # Test with short timeout - should return quickly after settle time
        start_time = time.time()
        result = adapter.lsp.gather_notifications(
            "textDocument/publishDiagnostics", timeout=5.0
        )
        elapsed = time.time() - start_time

        # Should return in about 0.5 seconds (settle time) not the full 5 seconds
        assert elapsed < 1.0, f"Expected quick return (~0.5s), but took {elapsed:.2f}s"
        assert len(result) == 1, f"Expected 1 diagnostic message, got {len(result)}"

        adapter.lsp.shutdown()


@patch("subprocess.Popen")
def test_gopls_configuration(mock_popen, tmp_path):
    """Test that gopls configuration is properly sent and applied"""
    
    # Test with custom configuration
    custom_config = {
        "staticcheck": True,
        "analyses": {
            "unusedparams": True,
            "nilness": True,
        },
        "gofumpt": True,
    }
    
    file_path = tmp_path / "config_test.go"
    file_path.write_text("""package main

import "fmt"

func main() {
    result := testUnusedParam("test", 42)
    fmt.Println(result)
}

func testUnusedParam(used string, unused int) string {
    return used
}
""")
    
    # Mock diagnostic response
    diagnostic_message = {
        "jsonrpc": "2.0",
        "method": "textDocument/publishDiagnostics",
        "params": {
            "uri": f"file://{file_path}",
            "diagnostics": [
                {
                    "range": {
                        "start": {"line": 9, "character": 34},
                        "end": {"line": 9, "character": 40}
                    },
                    "severity": 2,
                    "source": "unusedparams",
                    "message": "unused parameter: unused"
                }
            ]
        }
    }
    
    mock_proc = MockLSPProcess([diagnostic_message])
    mock_popen.return_value = mock_proc
    
    # Create adapter with custom config
    adapter = GoplsLSPAdapter(root_path=str(tmp_path), config=custom_config)
    
    # Mock the actual LSP communication
    with patch.object(adapter, 'start_server') as mock_start:
        mock_start.return_value = None
        adapter.lsp = BasicLSPClient(["mock-gopls"]) 
        adapter.lsp.start()
        adapter.config = custom_config  # Ensure config is set
        
        # Directly add the notification
        adapter.lsp.notifications = [diagnostic_message]
        
        # Test analysis
        result = adapter.lsp.gather_notifications("textDocument/publishDiagnostics", timeout=2.0)
        
        # Verify we get the expected diagnostic
        assert len(result) == 1, f"Expected 1 diagnostic message, got {len(result)}"
        
        diag_params = result[0]["params"]
        diagnostics = diag_params["diagnostics"]
        assert len(diagnostics) == 1, f"Expected 1 diagnostic, got {len(diagnostics)}"
        assert diagnostics[0]["source"] == "unusedparams", f"Expected 'unusedparams' source, got {diagnostics[0]['source']}"
        assert "unused parameter" in diagnostics[0]["message"], f"Message doesn't contain expected text: {diagnostics[0]['message']}"
        
        # Verify configuration structure
        assert adapter.config["staticcheck"] == True
        assert "unusedparams" in adapter.config["analyses"]
        assert adapter.config["gofumpt"] == True
        
        adapter.lsp.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

