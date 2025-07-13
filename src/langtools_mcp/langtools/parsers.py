import json
from typing import Dict, List


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
