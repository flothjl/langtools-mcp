from .analysis import BaseAnalyzer, register_analyzer
from .langtools_daemon_client import LangtoolsDaemonClient


class RuffAnalyzer(BaseAnalyzer):
    def analyze(self, file_path: str) -> dict:
        client = LangtoolsDaemonClient()
        return client.analyze(file_path, "python")


# Register RuffAnalyzer for python analysis so all python checks go via the daemon
register_analyzer("python", RuffAnalyzer)
