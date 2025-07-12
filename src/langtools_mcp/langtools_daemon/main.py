import json
import logging
import sys
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

from langtools_mcp.langtools_daemon.gopls_lsp_adapter import GoplsLSPAdapter
from langtools_mcp.langtools_daemon.lsp_adapter import find_go_module_root
from langtools_mcp.langtools_daemon.lsp_pool import LSPServerPool

HOST = "localhost"
PORT = 61782

# One pool for all requests
lsp_pool = LSPServerPool({"go": GoplsLSPAdapter})

logger = logging.getLogger("langtools_daemon")


class LangtoolsDaemonHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        logger.debug(f"Received request: {body.decode('utf-8')}")
        try:
            req = json.loads(body)
        except Exception as e:
            logger.error(f"JSON decode error: {e}")
            self.send_response(400)
            self.end_headers()
            self.safe_write(b"Invalid JSON")
            return

        file_path = req.get("file_path")
        language = req.get("language")
        logger.debug(f"file_path={file_path}, language={language}")
        if not file_path or not language:
            logger.warning("Missing file_path or language in request")
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
                    logger.error(f"Ruff preparation error: {err}")
                    self.send_response(500)
                    self.end_headers()
                    self.safe_write(f"Unable to prepare ruff: {err}".encode())
                    return
                result = run_ruff_analysis(ruff_path, file_path)
            elif language == "go":
                root = find_go_module_root(file_path)
                logger.debug(f"Using go module root: {root}")
                adapter = lsp_pool.get_server("go", root)
                result = adapter.analyze(file_path)
                logger.debug(f"gopls LSP Result: {result}")
            else:
                logger.warning(f"Language not supported: {language}")
                self.send_response(400)
                self.end_headers()
                self.safe_write(f"Language not supported: {language}".encode())
                return

            logger.debug(f"Result: {result}")
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.safe_write(json.dumps(result).encode())

        except BrokenPipeError:
            logger.error(
                "BrokenPipeError: Client disconnected before response could be delivered."
            )
            logger.debug(
                "Would have sent:",
                json.dumps(result) if result else "No result",
            )
        except Exception as exc:
            logger.exception(f"Exception: {exc}")
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_json = {"status": "fail", "error": f"LSP Adapter error: {exc}"}
            try:
                self.safe_write(json.dumps(error_json).encode())
            except BrokenPipeError:
                logger.error(
                    "BrokenPipeError when sending error JSON, client disconnected too soon."
                )

    def safe_write(self, data):
        try:
            self.wfile.write(data)
        except BrokenPipeError:
            logger.error(f"BrokenPipeError during write. Data was: {data!r}")


def run():
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, LangtoolsDaemonHandler)
    logger.info(f"LSP Daemon started on {HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down daemon...")
        httpd.server_close()


if __name__ == "__main__":
    run()
