import base64
import json
import os
import webbrowser
import zlib
from typing import List, Tuple
from urllib.parse import quote

from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import INVALID_REQUEST, ErrorData
from pydantic import BaseModel, FilePath

import lsp_mcp.lsp.ruff_analyzer  # ensures RuffAnalyzer is registered
from lsp_mcp.lsp.analysis import run_analysis_for_language

INSTRUCTIONS = """
Currently ONLY supports python
"""

mcp = FastMCP("MCP to allow llms to analyze their code", INSTRUCTIONS)


class AnalyzeFileParams(BaseModel):
    file_path: FilePath


@mcp.tool(
    "AnalyzeFile",
    description="Run a file through analysis. You MUST provide a valid Path for the file.",
)
def analyze_file(params: AnalyzeFileParams):
    try:
        analysis_result = run_analysis_for_language(str(params.file_path))
    except ValueError as e:
        raise McpError(ErrorData(message=str(e), code=INVALID_REQUEST))
    except NotImplementedError as e:
        raise McpError(ErrorData(message=str(e), code=INVALID_REQUEST))
    return analysis_result
