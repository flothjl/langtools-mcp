from .analysis import BaseAnalyzer, register_analyzer
from .langtools_daemon_client import LangtoolsDaemonClient


class GoAnalyzer(BaseAnalyzer):
    def analyze(self, file_path: str) -> dict:
        client = LangtoolsDaemonClient()
        return client.analyze(file_path, "go")


register_analyzer("go", GoAnalyzer)
