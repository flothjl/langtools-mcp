import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal

from langtools_mcp.langtools_daemon.gopls_lsp_adapter import GoplsLSPAdapter
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
    def analyze(self, project_root: str) -> Any:
        pass


def find_virtual_env(path: str) -> str | None:
    """
    Finds a virtual environment directory within the project root.
    Searches for common names like '.venv', 'venv', 'env'.
    """
    common_names = [".venv", "venv", "env", ".env"]
    for name in common_names:
        venv_path = Path(path) / name
        # Check for the activation script or python executable to confirm it's a venv
        if (venv_path / "bin" / "activate").exists() or (
            venv_path / "Scripts" / "activate.bat"
        ).exists():
            return str(venv_path)
    return None


def find_go_module_root(path: str) -> str:
    path = os.path.abspath(path)

    # If it's a file, get its containing directory
    if os.path.isfile(path):
        dir_path = os.path.dirname(path)
    else:
        dir_path = path

    while True:
        maybe_mod = os.path.join(dir_path, "go.mod")
        if os.path.isfile(maybe_mod):
            return dir_path
        parent = os.path.dirname(dir_path)
        if parent == dir_path:
            break  # Reached the filesystem root
        dir_path = parent

    # Fallback: return starting directory (normalized)
    return os.path.abspath(path)


def parse_pyright_output(output: str) -> List[Dict]:
    """
    Parses the JSON output from Pyright, extracting the list of
    diagnostics from the 'generalDiagnostics' key.
    """
    if not output.strip():
        return []

    data = json.loads(output)
    return data.get("generalDiagnostics", [])


def parse_as_json_document(output: str) -> List[Dict]:
    """Parses a single JSON document (e.g., a list of issues)."""
    if not output.strip():
        return []
    return json.loads(output)


def parse_as_json_stream(output: str) -> List[Dict]:
    """Parses a stream of JSON objects, one per line."""
    if not output.strip():
        return []
    return [json.loads(line) for line in output.strip().split("\n") if line]


def run_tool(
    cmd: List[str], cwd: str, parser: Callable[[str], Any] = lambda x: x
) -> List[Dict]:
    """
    Executes a tool and uses a provided parser function to process the output.
    """
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        output = proc.stdout if proc.stdout else proc.stderr
        logger.info(output)

        return parser(output)

    except FileNotFoundError:
        tool_name = cmd[0]
        logging.error(f"Error: The tool '{tool_name}' was not found.")
        return [
            {
                "source": "daemon_error",
                "file": tool_name,
                "message": f"Analysis tool '{tool_name}' is not installed or not in PATH.",
            }
        ]
    except Exception as e:
        logging.error(f"Failed to execute or parse for command '{' '.join(cmd)}': {e}")
        return []


class GoStrategy(LanguageStrategy):
    def analyze(self, project_root: str) -> Any:
        """
        Analyzes the entire Go project containing the given file.

        It finds the project root (where go.mod is located), then runs
        'go vet' on all packages within that module.
        """
        # 1. Find the project's root directory
        root = find_go_module_root(project_root)
        if not root:
            return {
                "status": "fail",
                "error": "Could not find a go.mod file for the project.",
            }

        logging.debug(f"Analyzing entire Go project at root: {root}")

        # 2. Run the analysis tools on all packages ('./...')
        vet_cmd = ["go", "vet", "-json", "./..."]

        vet_issues = run_tool(vet_cmd, cwd=root)

        # 3. Normalize the results into a single, consistent format
        normalized_results = []

        normalized_results.append({"source": "go vet", "output": vet_issues})

        return {"status": "ok", "diagnostics": normalized_results}


class PythonStrategy(LanguageStrategy):
    def analyze(self, project_root: str) -> Any:
        """
        Analyzes the entire Python project, using its virtual environment
        for accurate import resolution.
        """
        logging.debug(f"Analyzing entire Python project at root: {project_root}")

        venv_path = find_virtual_env(project_root)
        if venv_path:
            logging.debug(f"Found Python virtual environment at: {venv_path}")
        else:
            logging.warning(f"No virtual environment found for project: {project_root}")

        ruff_executable = "ruff"
        pyright_cmd = ["npx", "pyright", "--outputjson"]

        if venv_path:
            ruff_venv_executable = os.path.join(venv_path, "bin", "ruff")
            if os.path.exists(ruff_venv_executable):
                ruff_executable = ruff_venv_executable

            pyright_cmd.extend(
                ["--pythonpath", os.path.join(venv_path, "bin", "python")]
            )

        ruff_cmd = [
            ruff_executable,
            "check",
            ".",
            "--output-format=json",
            "--force-exclude",
        ]
        ruff_issues = run_tool(
            ruff_cmd, cwd=project_root, parser=parse_as_json_document
        )
        logger.info(f"{pyright_cmd}")
        pyright_issues = run_tool(
            pyright_cmd, cwd=project_root, parser=parse_pyright_output
        )

        normalized_results = []
        for issue in ruff_issues:
            normalized_results.append(
                {
                    "source": "ruff",
                    "code": issue.get("code"),
                    "file": issue.get("filename"),
                    "line": issue.get("location", {}).get("row"),
                    "column": issue.get("location", {}).get("column"),
                    "message": issue.get("message"),
                }
            )

        for issue in pyright_issues:
            normalized_results.append(
                {
                    "source": "pyright",
                    "code": issue.get("rule"),
                    "file": issue.get("file"),
                    "line": issue.get("range", {}).get("start", {}).get("line"),
                    "column": issue.get("range", {}).get("start", {}).get("character"),
                    "message": issue.get("message"),
                }
            )

        return {"status": "ok", "diagnostics": normalized_results}


class LanguageHandler:
    def __init__(self, language_strategy: LanguageStrategy):
        self._language_strategy = language_strategy

    @property
    def language_strategy(self):
        return self._language_strategy

    @language_strategy.setter
    def language_strategy(self, v):
        self._language_strategy = v

    def analyze(self, project_root: str):
        return self._language_strategy.analyze(project_root)

    @classmethod
    def from_language(cls, language: str):
        LANGUAGE_MAP = {"go": GoStrategy, "python": PythonStrategy}
        if language.lower() not in LANGUAGE_MAP:
            raise UnsupportedLanguageException(f"Filetype {language} not supported")

        return cls(LANGUAGE_MAP[language.lower()]())


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

        language = req.get("language")
        project_root = req.get("project_root")
        logger.debug(f"language={language}")
        if not language or not project_root:
            logger.warning("Missing language or project root in request")
            self.send_response(400)
            self.end_headers()
            self.safe_write(b"Missing language or project root")
            return

        result = None
        try:
            lang_strategy = LanguageHandler.from_language(language)
            result = lang_strategy.analyze(project_root)
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
        except UnsupportedLanguageException:
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
    host: str = os.getenv("LANGTOOLSD_HOST", HOST)
    port = int(os.getenv("LANGTOOLSD_PORT", PORT))
    server_address = (host, port)
    httpd = HTTPServer(server_address, LangtoolsDaemonHandler)
    logger.info(f"LSP Daemon started on {HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down daemon...")
        httpd.server_close()


if __name__ == "__main__":
    run()
