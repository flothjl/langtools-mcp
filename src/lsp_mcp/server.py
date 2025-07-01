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

INSTRUCTIONS = """

"""

mcp = FastMCP("MCP to allow llms to analyze their code", INSTRUCTIONS)


class AnalyzeFileParams(BaseModel):
    file_path: FilePath


@mcp.tool("AnalyzeFile")
def analyze_file(params: AnalyzeFileParams):
    # TODO: implement
    return
