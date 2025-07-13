import logging
import threading

logger = logging.getLogger(__name__)


class LSPServerPool:
    def __init__(self, adapter_classes):
        """
        adapter_classes: dict mapping language string to LSP adapter class.
        Example: {"go": GoplsLSPAdapter, ...}
        """
        self.adapter_classes = adapter_classes
        self.lock = threading.Lock()
        self.servers = {}  # (language, root) -> adapter instance

    def get_server(self, language, root_path, **kwargs):
        with self.lock:
            key = (language, root_path)
            if key not in self.servers:
                logger.info(
                    f"Spawning new {language} LSP for root={root_path}",
                )
                adapter_cls = self.adapter_classes[language]
                self.servers[key] = adapter_cls(root_path=root_path, **kwargs)
            return self.servers[key]

    def shutdown(self):
        with self.lock:
            for srv in self.servers.values():
                srv.shutdown()
            self.servers.clear()
