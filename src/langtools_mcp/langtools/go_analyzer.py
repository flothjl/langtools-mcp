from .analysis import BaseAnalyzer, register_analyzer
from .lsp_daemon_client import LSPDaemonClient

class GoAnalyzer(BaseAnalyzer):
    def analyze(self, file_path: str) -> dict:
        client = LSPDaemonClient()
        return client.analyze(file_path, "go")

register_analyzer("go", GoAnalyzer)
