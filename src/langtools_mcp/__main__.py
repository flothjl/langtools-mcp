import argparse
import json
import langtools_mcp.lsp.ruff_analyzer  # Register Ruff/Python analyzer on import
from langtools_mcp.lsp.analysis import run_analysis_for_language


def main():
    parser = argparse.ArgumentParser(description="Test AnalyzeFile tool")
    parser.add_argument("file", help="Python file to analyze")
    args = parser.parse_args()
    try:
        output = run_analysis_for_language(args.file)
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
