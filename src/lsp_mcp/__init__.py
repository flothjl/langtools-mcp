import atexit
import signal
import subprocess
import sys

from .server import mcp


def start_lsp_daemon():
    proc = subprocess.Popen(
        [sys.executable, "-u", "-m", "lsp_mcp.lsp_daemon.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    def cleanup():
        print("Shutting down LSP daemon...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    atexit.register(cleanup)

    def sig_handler(signum, frame):
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)
    return proc


def main():
    print("Starting LSP daemon sidecar...")
    _daemon_proc = start_lsp_daemon()
    mcp.run()


if __name__ == "__main__":
    main()
