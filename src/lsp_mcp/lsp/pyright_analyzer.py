import subprocess
import json
from .analysis import BaseAnalyzer, register_analyzer

class PyrightAnalyzer(BaseAnalyzer):
    def analyze(self, file_path: str) -> dict:
        cmd = ["pyright", file_path, "--outputjson"]
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,  # pyright returns nonzero if any issues, but we want the output
                encoding="utf-8"
            )
        except Exception as exc:
            return {"error": f"Failed to run pyright: {exc}"}
        # If pyright wasn't found
        if proc.returncode == 127 or "pyright: command not found" in proc.stderr:
            return {"error": "pyright is not installed or not found in PATH."}
        try:
            output = json.loads(proc.stdout)
        except Exception as exc:
            return {"error": f"pyright output could not be parsed: {exc}", "stdout": proc.stdout, "stderr": proc.stderr}
        # Extract diagnostics for the file
        diag = [d for d in output.get("generalDiagnostics", []) if d.get("file") == file_path]
        errors = [d for d in diag if d.get("severity") == "error"]
        warnings = [d for d in diag if d.get("severity") == "warning"]
        deprecations = [d for d in diag if "deprecat" in (d.get("message", "").lower())]
        return {
            "summary": {
                "errors": len(errors),
                "warnings": len(warnings),
                "deprecations": len(deprecations),
            },
            "errors": errors,
            "warnings": warnings,
            "deprecations": deprecations,
            "raw": output,
        }

register_analyzer("python", PyrightAnalyzer)
