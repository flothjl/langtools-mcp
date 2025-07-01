from .server import mcp

def main():
    mcp.run()

if __name__ == "__main__":
    import argparse
    import json
    from lsp_mcp.lsp.analysis import run_analysis_for_language
    parser = argparse.ArgumentParser(description="Test AnalyzeFile tool")
    parser.add_argument("file", help="Python file to analyze")
    args = parser.parse_args()
    try:
        output = run_analysis_for_language(args.file)
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(f"Error: {e}")
