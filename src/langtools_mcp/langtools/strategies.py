import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Literal, Type

from pydantic import BaseModel

from langtools_mcp.langtools.parsers import (
    parse_as_json_document,
    parse_pyright_output,
)
from langtools_mcp.langtools.settings import GoToolSettings, PythonToolSettings
from langtools_mcp.langtools.tool_runner import ToolRunner
from langtools_mcp.langtools.utils import (
    NoRootFoundException,
    find_go_module_root,
    find_ts_root,
    find_virtual_env,
)

logger = logging.getLogger(__name__)


class ToolSetupError(Exception): ...


class UnsupportedLanguageException(Exception): ...


class Diagnostic(BaseModel):
    status: Literal["ok", "failure"]
    source: str
    output: Any


class AnalysisResponse(BaseModel):
    status: Literal["ok", "fail"]
    diagnostics: list[Diagnostic]


class LanguageStrategy(ABC):
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.available_tools: Dict[str, Callable[[], Diagnostic]] = {}

    def analyze(self) -> AnalysisResponse:
        logger.debug(f"Analyzing entire Python project at root: {self.project_root}")
        normalized_results = []
        for tool in self.configured_tools:
            normalized_results.append(self.call_tool_safely(tool))
        return AnalysisResponse(status="ok", diagnostics=normalized_results)

    def call_tool_safely(self, tool_name: str):
        try:
            return self.available_tools[tool_name]()
        except KeyError:
            logger.exception(f"Unable to find tool for {tool_name}")
            return Diagnostic(
                status="ok",
                source=tool_name,
                output="Unable to find tool. Analysis was skipped for this tool",
            )

    @property
    @abstractmethod
    def configured_tools(self) -> List[Any]: ...


class TypescriptStrategy(LanguageStrategy):
    def analyze(self) -> Any:
        try:
            root = find_ts_root(self.project_root)
        except NoRootFoundException:
            return {
                "status": "fail",
                "error": "Could not find a typescript root directory in this project.",
            }
        runner = ToolRunner(root)
        tsc_issues = runner.run(["npx", "tsc", "--noEmit"])
        eslint_issues = runner.run(["npx", "eslint", "--ext", ".js,.jsx,.ts,.tsx"])
        return {
            "status": "ok",
            "diagnostics": [
                {"source": "tsc", "output": tsc_issues},
                {"source": "eslint", "output": eslint_issues},
            ],
        }


class GoStrategy(LanguageStrategy):
    def __init__(self, project_root: str):
        super().__init__(project_root)

        self.available_tools = {"vet": self.run_go_vet}

    @property
    def configured_tools(self) -> List[Any]:
        return GoToolSettings().GO_TOOLS

    def run_go_vet(self):
        root = find_go_module_root(self.project_root)
        if not root:
            return Diagnostic(
                status="failure",
                source="vet",
                output="Could not find go.mod file for the project",
            )

        logger.debug(f"Analyzing entire Go project at root: {root}")
        runner = ToolRunner(root, GoToolSettings().BIN_DIR)
        vet_issues = runner.run(["go", "vet", "-json", "./..."])
        return Diagnostic(status="ok", source="vet", output=vet_issues)


class PythonStrategy(LanguageStrategy):
    def __init__(self, project_root: str):
        super().__init__(project_root)
        self.venv_path = find_virtual_env(self.project_root)
        if self.venv_path:
            logger.debug(f"Found Python virtual environment at: {self.venv_path}")
        else:
            logger.warning("No virtual environment found.")

        self.available_tools = {"ruff": self.run_ruff, "pyright": self.run_pyright}

    @property
    def configured_tools(self) -> List[Any]:
        return PythonToolSettings().TOOLS

    def run_ruff(self):
        ruff_executable = "ruff"

        if self.venv_path:
            ruff_venv_executable = os.path.join(self.venv_path, "bin", "ruff")
            if os.path.exists(ruff_venv_executable):
                ruff_executable = ruff_venv_executable

        runner = ToolRunner(self.project_root, PythonToolSettings().BIN_DIR)
        ruff_issues = runner.run(
            [ruff_executable, "check", ".", "--output-format=json", "--force-exclude"],
            parser=parse_as_json_document,
        )

        return Diagnostic(status="ok", source="ruff", output=ruff_issues)

    def run_pyright(self):
        pyright_cmd = ["npx", "pyright", "--outputjson"]

        if self.venv_path:
            pyright_cmd.extend(
                ["--pythonpath", os.path.join(self.venv_path, "bin", "python")]
            )

        runner = ToolRunner(self.project_root, PythonToolSettings().BIN_DIR)
        pyright_issues = runner.run(pyright_cmd, parser=parse_pyright_output)

        return Diagnostic(status="ok", source="pyright", output=pyright_issues)


LANGUAGE_STRATEGIES: Dict[str, Type[LanguageStrategy]] = {
    "go": GoStrategy,
    "python": PythonStrategy,
    "javascript": TypescriptStrategy,
    "typescript": TypescriptStrategy,
}
