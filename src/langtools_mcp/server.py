import logging
from typing import Literal

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_REQUEST, ErrorData
from pydantic import BaseModel

from langtools_mcp.langtools.analysis import run_analysis_for_language
from langtools_mcp.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

INSTRUCTIONS = """
currently supports the following languages:
    - python
    - golang
    - typescript/javascript
When passing a `project_root` you MUST pass a full absolute path to the root of the project you are analyzing.
For monorepos, be sure to pass the project within the repo you want analysis on. 
"""

mcp = FastMCP("MCP to allow llms to analyze their code", INSTRUCTIONS)


class AnalyzeFileParams(BaseModel):
    language: Literal["python", "go", "typescript", "javascript"]
    project_root: str


@mcp.tool(
    "AnalyzeCodebase",
    description="Run a codebase through analysis for a given language. ",
)
def analyze_codebase(params: AnalyzeFileParams):
    try:
        analysis_result = run_analysis_for_language(
            language=params.language, project_root=params.project_root
        )
    except ValueError as e:
        raise McpError(ErrorData(message=str(e), code=INVALID_REQUEST))
    except NotImplementedError as e:
        raise McpError(ErrorData(message=str(e), code=INVALID_REQUEST))
    return analysis_result
