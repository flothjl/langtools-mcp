import json
import logging
import sys
import traceback
from abc import ABC, abstractmethod
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from langtools_mcp.langtools_daemon.gopls_lsp_adapter import GoplsLSPAdapter
from langtools_mcp.langtools_daemon.lsp_adapter import find_go_module_root
from langtools_mcp.langtools_daemon.lsp_pool import LSPServerPool

HOST = "localhost"
PORT = 61782

# One pool for all requests
lsp_pool = LSPServerPool({"go": GoplsLSPAdapter})

logger = logging.getLogger("langtools_daemon")


class ToolSetupError(Exception): ...


class UnsupportedLanguageException(Exception): ...


class LanguageStrategy(ABC):
    @abstractmethod
    def analyze_file(self, file_path: str) -> Any:
        pass


class GoStrategy(LanguageStrategy):
    def analyze_file(self, file_path: str) -> Any:
        root = find_go_module_root(file_path)
        logger.debug(f"Using go module root: {root}")
        adapter = lsp_pool.get_server("go", root)
        result = adapter.analyze(file_path)
        return result


class PythonStrategy(LanguageStrategy):
    def analyze_file(self, file_path: str):
        from langtools_mcp.langtools_daemon.ruff_runner import (
            ensure_ruff,
            run_ruff_analysis,
        )

        ruff_path, err = ensure_ruff()
        if err is not None:
            raise ToolSetupError(f"Unable to prepare ruff: {err}")
        return run_ruff_analysis(ruff_path, file_path)


class LanguageHandler:
    def __init__(self, language_strategy: LanguageStrategy):
        self._language_strategy = language_strategy

    @property
    def language_strategy(self):
        return self._language_strategy

    @language_strategy.setter
    def language_strategy(self, v):
        self._language_strategy = v

    def analyze_file(self, file_path: str):
        return self._language_strategy.analyze_file(file_path)

    @classmethod
    def from_extension(cls, file_extension: str):
        EXT_MAP = {"go": GoStrategy, "python": PythonStrategy}
        if file_extension.lower() not in EXT_MAP:
            raise UnsupportedLanguageException(
                f"Filetype {file_extension} not supported"
            )

        return cls(EXT_MAP[file_extension.lower()]())


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
            lang_strategy = LanguageHandler.from_extension(language)
            result = lang_strategy.analyze_file(file_path)
            logger.debug(f"Result: {result}")
            logger.debug(f"lang strat: {lang_strategy.language_strategy!r}")
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
        except UnsupportedLanguageException as exc:
            logger.warning(f"Language not supported: {language}")
            self.send_response(400)
            self.end_headers()
            self.safe_write(f"Language not supported: {language}".encode())
        except Exception as exc:
            logger.exception(f"Exception: {exc}")
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_json = {"status": "fail", "error": f"LSP Adapter error: {exc}"}
            self.safe_write(json.dumps(error_json).encode())

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
