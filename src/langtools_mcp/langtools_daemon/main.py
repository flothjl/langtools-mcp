import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from langtools_mcp.langtools.strategies import LANGUAGE_STRATEGIES
from langtools_mcp.logger import setup_logging

HOST = "localhost"
PORT = 61782

setup_logging()
logger = logging.getLogger("langtools_daemon")


class LangtoolsDaemonHandler(BaseHTTPRequestHandler):
    def send_error_json(self, code, message):
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "fail", "error": message}).encode())

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length)
            req = json.loads(data)
            language = req.get("language")
            project_root = req.get("project_root")
            logger.info(
                f"POST request: language={language}, project_root={project_root}"
            )
            if not language or not project_root:
                self.send_error_json(400, "Missing language or project_root")
                return
            try:
                strategy_cls = LANGUAGE_STRATEGIES[language.lower()]
                strategy = strategy_cls(project_root)
            except KeyError:
                self.send_error_json(400, f"Unsupported language: {language}")
                return
            result = strategy.analyze()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(result.model_dump_json().encode())
        except Exception as exc:
            logger.exception("Unhandled exception")
            self.send_error_json(500, str(exc))


def run():
    host = os.getenv("LANGTOOLSD_HOST", HOST)
    port = int(os.getenv("LANGTOOLSD_PORT", PORT))
    server_address = (host, port)
    httpd = HTTPServer(server_address, LangtoolsDaemonHandler)
    logger.info(f"Langtools Daemon started on {host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down daemon...")
        httpd.server_close()


if __name__ == "__main__":
    run()
