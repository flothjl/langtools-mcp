import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
import traceback
from langtools_mcp.langtools_daemon.lsp_pool import LSPServerPool
from langtools_mcp.langtools_daemon.gopls_lsp_adapter import GoplsLSPAdapter
from langtools_mcp.langtools_daemon.lsp_adapter import find_go_module_root

HOST = "localhost"
PORT = 61782

# One pool for all requests
lsp_pool = LSPServerPool({"go": GoplsLSPAdapter})

class LangtoolsDaemonHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        print(f"\n[DAEMON] Received request: {body.decode('utf-8')}", file=sys.stderr)
        try:
            req = json.loads(body)
        except Exception as e:
            print(f"[DAEMON] JSON decode error: {e}", file=sys.stderr)
            self.send_response(400)
            self.end_headers()
            self.safe_write(b"Invalid JSON")
            return

        file_path = req.get("file_path")
        language = req.get("language")
        print(f"[DAEMON] file_path={file_path}, language={language}", file=sys.stderr)
        if not file_path or not language:
            print("[DAEMON] Missing file_path or language", file=sys.stderr)
            self.send_response(400)
            self.end_headers()
            self.safe_write(b"Missing file_path or language")
            return
        result = None
        try:
            if language == "python":
                from langtools_mcp.langtools_daemon.ruff_runner import (
                    ensure_ruff,
                    run_ruff_analysis,
                )
                ruff_path, err = ensure_ruff()
                if err is not None:
                    print(f"[DAEMON] Ruff error: {err}", file=sys.stderr)
                    self.send_response(500)
                    self.end_headers()
                    self.safe_write(f"Unable to prepare ruff: {err}".encode())
                    return
                result = run_ruff_analysis(ruff_path, file_path)
            elif language == "go":
                root = find_go_module_root(file_path)
                print(f"[DAEMON] Using go module root: {root}", file=sys.stderr)
                adapter = lsp_pool.get_server("go", root)
                result = adapter.analyze(file_path)
                print(f"[DAEMON] gopls LSP Result: {result}", file=sys.stderr)
            else:
                print(f"[DAEMON] Language not supported: {language}", file=sys.stderr)
                self.send_response(400)
                self.end_headers()
                self.safe_write(f"Language not supported: {language}".encode())
                return
            print(f"[DAEMON] Result: {result}", file=sys.stderr)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.safe_write(json.dumps(result).encode())
        except BrokenPipeError:
            print(f"[DAEMON EXCEPTION] BrokenPipeError: Client disconnected before response could be delivered.", file=sys.stderr)
            print("[DAEMON] Would have sent:", json.dumps(result) if result else "No result", file=sys.stderr)
        except Exception as exc:
            print(f"[DAEMON EXCEPTION] {exc}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_json = {"status": "fail", "error": f"LSP Adapter error: {exc}"}
            try:
                self.safe_write(json.dumps(error_json).encode())
            except BrokenPipeError:
                print("[DAEMON EXCEPTION] BrokenPipeError when sending error JSON, client disconnected too soon.", file=sys.stderr)

    def safe_write(self, data):
        try:
            self.wfile.write(data)
        except BrokenPipeError:
            print(f"[DAEMON EXCEPTION] BrokenPipeError during write. Data was: {data!r}", file=sys.stderr)

def run():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, LangtoolsDaemonHandler)
    print(f"LSP Daemon started on {HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down daemon...")
        httpd.server_close()

if __name__ == "__main__":
    run()
