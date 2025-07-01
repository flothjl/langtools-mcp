from .analysis import BaseAnalyzer, register_analyzer
from .lsp_daemon_client import LSPDaemonClient

class RuffAnalyzer(BaseAnalyzer):
    def analyze(self, file_path: str) -> dict:
        client = LSPDaemonClient()
        return client.analyze(file_path, "python")

# Register RuffAnalyzer for python analysis so all python checks go via the daemon
register_analyzer("python", RuffAnalyzer)
