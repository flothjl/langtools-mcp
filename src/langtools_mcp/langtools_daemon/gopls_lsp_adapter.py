import logging
import os
import time

from .lsp_adapter import BasicLSPClient

logger = logging.getLogger(__name__)

DEFAULT_GOPLS_CONFIG = {
    "gofumpt": True,
    "codelenses": {
        "gc_details": False,
        "generate": True,
        "regenerate_cgo": True,
        "run_govulncheck": True,
        "test": True,
        "tidy": True,
        "upgrade_dependency": True,
        "vendor": True,
    },
    "hints": {
        "assignVariableTypes": True,
        "compositeLiteralFields": True,
        "compositeLiteralTypes": True,
        "constantValues": True,
        "functionTypeParameters": True,
        "parameterNames": True,
        "rangeVariableTypes": True,
    },
    "analyses": {
        "nilness": True,
        "unusedparams": True,
        "unusedwrite": True,
        "useany": True,
    },
    "usePlaceholders": True,
    "completeUnimported": True,
    "staticcheck": True,
    "directoryFilters": [
        "-.git",
        "-.vscode",
        "-.idea",
        "-.vscode-test",
        "-node_modules",
    ],
    "semanticTokens": True,
}


class GoplsLSPAdapter:
    def __init__(self, root_path, gopls_path="gopls", config=None):
        self.root_path = root_path
        self.gopls_path = gopls_path
        self.lsp = None  # Will start on first analyze
        self.started = False
        self.config = config or DEFAULT_GOPLS_CONFIG

    def start_server(self):
        if not self.started:
            logger.info(
                f"Starting gopls for root={self.root_path}",
            )
            self.lsp = BasicLSPClient([self.gopls_path])
            self.lsp.start()
            root_uri = "file://" + self.root_path

            # Enhanced initialization with gopls configuration
            init_params = {
                "rootUri": root_uri,
                "capabilities": {
                    "textDocument": {
                        "publishDiagnostics": {
                            "relatedInformation": True,
                            "tagSupport": {"valueSet": [1, 2]},
                            "codeDescriptionSupport": True,
                            "dataSupport": True,
                        }
                    }
                },
                "processId": None,
                "initializationOptions": self.config,
            }

            init_resp = self.lsp.send_request("initialize", init_params)
            logger.info(f"initialize resp: {init_resp}")

            # Send initialized notification
            self.lsp.send_notification("initialized", {})

            # Send workspace configuration (alternative/additional method)
            self.lsp.send_notification(
                "workspace/didChangeConfiguration", {"settings": {"gopls": self.config}}
            )

            logger.info(
                f"Sent gopls configuration: {self.config}",
            )
            time.sleep(0.5)
            self.started = True

    def analyze(self, file_path):
        try:
            self.start_server()
            with open(file_path) as f:
                file_content = f.read()
            logger.info(f"Analyzing {file_path}")
            self.lsp.send_notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": f"file://{os.path.abspath(file_path)}",
                        "languageId": "go",
                        "version": 1,
                        "text": file_content,
                    }
                },
            )
            logger.info("Sent didOpen notification")

            # Collect ALL diagnostic messages (not just the first one)
            diags = self.lsp.gather_notifications(
                "textDocument/publishDiagnostics", timeout=10.0
            )
            logger.info(
                f"Received {len(diags)} diagnostic messages",
            )

            # Count total diagnostics across all messages
            total_diagnostics = 0
            diagnostic_sources = set()
            for diag_msg in diags:
                params = diag_msg.get("params", {})
                if "diagnostics" in params:
                    diagnostics = params["diagnostics"]
                    total_diagnostics += len(diagnostics)
                    for diag in diagnostics:
                        source = diag.get("source", "unknown")
                        diagnostic_sources.add(source)

            logger.info(
                f"Total diagnostics: {total_diagnostics} from sources: {list(diagnostic_sources)}",
            )

            # Optionally send didClose to minimize memory in big servers
            # self.lsp.send_notification("textDocument/didClose", {...})

            if diags:
                return {
                    "status": "ok",
                    "diagnostics": diags,
                    "summary": {
                        "total_messages": len(diags),
                        "total_diagnostics": total_diagnostics,
                        "sources": list(diagnostic_sources),
                    },
                }
            else:
                logger.info("No diagnostics received.")
                return {"status": "ok", "note": "No diagnostics received from gopls."}
        except Exception as e:
            logger.exception("Exception occurred")
            return {"status": "fail", "error": f"Exception in analyzer: {e}"}

    def shutdown(self):
        if self.lsp:
            self.lsp.shutdown()
            self.lsp = None
            self.started = False
