from typing import List, Literal, Tuple
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_REQUEST, ErrorData
from pydantic import BaseModel, Field, FilePath

from langtools_mcp.langtools.analysis import run_analysis_for_language
from langtools_mcp.logger import setup_logging

logger = setup_logging()

INSTRUCTIONS = """
currently supports the following languages:
    - python
    - golang.
When passing a `file_path` you MUST pass a full absolute path to the file. 
"""

mcp = FastMCP("MCP to allow llms to analyze their code", INSTRUCTIONS)


class AnalyzeFileParams(BaseModel):
    language: Literal["python", "golang"]
    project_root: str


@mcp.tool(
    "Analyze",
    description="Run a project through analysis for a given language. ",
)
def analyze(params: AnalyzeFileParams):
    try:
        analysis_result = run_analysis_for_language(
            language=params.language, project_root=params.project_root
        )
    except ValueError as e:
        raise McpError(ErrorData(message=str(e), code=INVALID_REQUEST))
    except NotImplementedError as e:
        raise McpError(ErrorData(message=str(e), code=INVALID_REQUEST))
    return analysis_result
