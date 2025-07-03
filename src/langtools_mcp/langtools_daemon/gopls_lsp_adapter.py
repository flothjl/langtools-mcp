import os
import sys
import time
import traceback

from .lsp_adapter import BasicLSPClient


class GoplsLSPAdapter:
    def __init__(self, root_path, gopls_path="gopls"):
        self.root_path = root_path
        self.gopls_path = gopls_path
        self.lsp = None  # Will start on first analyze
        self.started = False

    def start_server(self):
        if not self.started:
            print(
                f"[GoplsLSPAdapter] Starting gopls for root={self.root_path}",
                file=sys.stderr,
            )
            self.lsp = BasicLSPClient([self.gopls_path])
            self.lsp.start()
            root_uri = "file://" + self.root_path
            init_resp = self.lsp.send_request(
                "initialize",
                {"rootUri": root_uri, "capabilities": {}, "processId": None},
            )
            print(f"[GOPLS ADAPTER] initialize resp: {init_resp}", file=sys.stderr)
            self.lsp.send_notification("initialized", {})
            time.sleep(0.5)
            self.started = True

    def analyze(self, file_path):
        try:
            self.start_server()
            with open(file_path) as f:
                file_content = f.read()
            print(f"[GOPLS ADAPTER] Analyzing {file_path}", file=sys.stderr)
            self.lsp.send_notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": f"file://{os.path.abspath(file_path)}",
                        "languageId": "go",
                        "version": 1,
                        "text": file_content,
                    }
                },
            )
            print("[GOPLS ADAPTER] Sent didOpen notification", file=sys.stderr)
            diags = self.lsp.gather_notifications(
                "textDocument/publishDiagnostics", timeout=5.0
            )
            print(f"[GOPLS ADAPTER] diags: {diags}", file=sys.stderr)
            # Optionally send didClose to minimize memory in big servers
            # self.lsp.send_notification("textDocument/didClose", {...})
            if diags:
                return {"status": "ok", "diagnostics": diags}
            else:
                print("[GOPLS ADAPTER] No diagnostics received.", file=sys.stderr)
                return {"status": "ok", "note": "No diagnostics received from gopls."}
        except Exception as e:
            print(f"[GOPLS ADAPTER EXCEPTION] {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return {"status": "fail", "error": f"Exception in analyzer: {e}"}

    def shutdown(self):
        if self.lsp:
            self.lsp.shutdown()
            self.lsp = None
            self.started = False
