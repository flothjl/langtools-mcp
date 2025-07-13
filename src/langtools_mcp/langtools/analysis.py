from langtools_mcp.langtools.langtools_daemon_client import LangtoolsDaemonClient


def run_analysis_for_language(language: str, project_root: str) -> dict:
    client = LangtoolsDaemonClient()
    return client.analyze(language, project_root)
