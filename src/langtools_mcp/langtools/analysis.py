from abc import ABC, abstractmethod

from langtools_mcp.langtools.langtools_daemon_client import LangtoolsDaemonClient


class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, file_path: str) -> dict:
        """
        Analyze the file and return structured results.
        """
        pass


def run_analysis_for_language(language: str, project_root: str) -> dict:
    client = LangtoolsDaemonClient()
    return client.analyze(language, project_root)
