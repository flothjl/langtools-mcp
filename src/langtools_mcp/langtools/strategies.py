import logging
import os
from abc import ABC, abstractmethod
from typing import Any

from langtools_mcp.langtools.parsers import (
    parse_as_json_document,
    parse_pyright_output,
)
from langtools_mcp.langtools.tool_runner import ToolRunner
from langtools_mcp.langtools.utils import find_go_module_root, find_virtual_env

logger = logging.getLogger(__name__)


class ToolSetupError(Exception): ...


class UnsupportedLanguageException(Exception): ...


class LanguageStrategy(ABC):
    @abstractmethod
    def analyze(self, project_root: str) -> Any:
        pass


class GoStrategy(LanguageStrategy):
    def analyze(self, project_root: str) -> Any:
        root = find_go_module_root(project_root)
        if not root:
            return {
                "status": "fail",
                "error": "Could not find a go.mod file for the project.",
            }

        logger.debug(f"Analyzing entire Go project at root: {root}")
        runner = ToolRunner(root)
        vet_issues = runner.run(["go", "vet", "-json", "./..."])
        return {
            "status": "ok",
            "diagnostics": [{"source": "go vet", "output": vet_issues}],
        }


class PythonStrategy(LanguageStrategy):
    def analyze(self, project_root: str) -> Any:
        logger.debug(f"Analyzing entire Python project at root: {project_root}")
        venv_path = find_virtual_env(project_root)

        if venv_path:
            logger.debug(f"Found Python virtual environment at: {venv_path}")
        else:
            logger.warning("No virtual environment found.")

        ruff_executable = "ruff"
        pyright_cmd = ["npx", "pyright", "--outputjson"]

        if venv_path:
            ruff_venv_executable = os.path.join(venv_path, "bin", "ruff")
            if os.path.exists(ruff_venv_executable):
                ruff_executable = ruff_venv_executable
            pyright_cmd.extend(
                ["--pythonpath", os.path.join(venv_path, "bin", "python")]
            )

        runner = ToolRunner(project_root)
        ruff_issues = runner.run(
            [ruff_executable, "check", ".", "--output-format=json", "--force-exclude"],
            parser=parse_as_json_document,
        )
        pyright_issues = runner.run(pyright_cmd, parser=parse_pyright_output)

        normalized_results = [{"source": "ruff", "output": ruff_issues}]

        normalized_results += [{"source": "pyright", "output": pyright_issues}]

        return {"status": "ok", "diagnostics": normalized_results}


LANGUAGE_STRATEGIES = {
    "go": GoStrategy,
    "python": PythonStrategy,
}
