import os
import sys
import json
import shutil
from http.server import BaseHTTPRequestHandler, HTTPServer
from lsp_mcp.lsp_daemon.ruff_runner import ensure_ruff, run_ruff_analysis

HOST = "localhost"
PORT = 61782

class LSPDaemonHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            req = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return
        
        file_path = req.get("file_path")
        language = req.get("language")
        if not file_path or not language:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing file_path or language")
            return
        result = None
        if language == "python":
            ruff_path, err = ensure_ruff()
            if err is not None:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Unable to prepare ruff: {err}".encode())
                return
            result = run_ruff_analysis(ruff_path, file_path)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Language not supported: {language}".encode())
            return

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())


def run():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, LSPDaemonHandler)
    print(f"LSP Daemon started on {HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down daemon...")
        httpd.server_close()

if __name__ == "__main__":
    run()
