import logging
import subprocess
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class ToolRunner:
    def __init__(self, cwd: str):
        self.cwd = cwd

    def run(
        self, cmd: List[str], parser: Callable[[str], Any] = lambda x: x
    ) -> List[Dict]:
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.cwd,
                capture_output=True,
                encoding="utf-8",
                check=False,
            )
            output = proc.stdout if proc.stdout else proc.stderr
            logger.info(output)
            return parser(output)

        except FileNotFoundError:
            tool_name = cmd[0]
            logger.error(f"Error: The tool '{tool_name}' was not found.")
            return [
                {
                    "source": "daemon_error",
                    "file": tool_name,
                    "message": f"Analysis tool '{tool_name}' is not installed or not in PATH.",
                }
            ]
        except Exception as e:
            logger.error(
                f"Failed to execute or parse for command '{' '.join(cmd)}': {e}"
            )
            return []
