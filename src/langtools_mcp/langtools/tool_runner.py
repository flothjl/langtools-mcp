import logging
import os
import shutil
import subprocess
from typing import Any, Callable, Dict, List, Union

logger = logging.getLogger(__name__)


class ToolRunner:
    def __init__(self, cwd: str, bin_dir: Union[str, List[str], None] = None):
        self.cwd = cwd
        if bin_dir is None:
            self.bin_dirs = []
        elif isinstance(bin_dir, str):
            self.bin_dirs = [bin_dir]
        else:
            self.bin_dirs = list(bin_dir)

    def run(
        self, cmd: List[str], parser: Callable[[str], Any] = lambda x: x
    ) -> List[Dict]:
        try:
            env = os.environ.copy()
            if self.bin_dirs:
                env["PATH"] = os.pathsep.join(self.bin_dirs + [env.get("PATH", "")])
            # Resolve executable using PATH
            tool_path = shutil.which(cmd[0], path=env["PATH"])
            if tool_path:
                cmd[0] = tool_path
            logger.debug(
                f"Running: {' '.join(cmd)} (CWD={self.cwd}) (PATH={env['PATH']})"
            )
            proc = subprocess.run(
                cmd,
                cwd=self.cwd,
                capture_output=True,
                encoding="utf-8",
                check=False,
            )
            output = proc.stdout if proc.stdout else proc.stderr
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
            return [
                {
                    "source": "daemon_error",
                    "file": cmd[0],
                    "message": str(e),
                }
            ]
