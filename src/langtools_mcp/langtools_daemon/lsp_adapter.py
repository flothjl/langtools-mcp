import json
import os
import subprocess
import sys
import threading
import time
import uuid


def find_go_module_root(file_path):
    dir_path = os.path.abspath(os.path.dirname(file_path))
    while True:
        maybe_mod = os.path.join(dir_path, "go.mod")
        if os.path.isfile(maybe_mod):
            return dir_path
        parent = os.path.dirname(dir_path)
        if parent == dir_path:
            break
        dir_path = parent
    # Fallback: file's parent
    return os.path.abspath(os.path.dirname(file_path))


class BasicLSPClient:
    def __init__(self, server_cmd):
        self.server_cmd = server_cmd
        self.proc = None
        self.reader_thread = None
        self.responses = {}
        self.response_events = {}  # id -> threading.Event
        self.notifications = []
        self.notifications_event = threading.Event()
        self._buffer = b""
        self._running = False

    def start(self):
        self.proc = subprocess.Popen(
            self.server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self._running = True
        self.reader_thread = threading.Thread(target=self._reader)
        self.reader_thread.daemon = True
        self.reader_thread.start()

    def _reader(self):
        while self._running:
            try:
                length_line = self.proc.stdout.readline()
                if not length_line:
                    break
                if length_line.lower().startswith(b"content-length:"):
                    length = int(length_line.split(b":")[1].strip())
                    self.proc.stdout.readline()  # blank line
                    payload = self.proc.stdout.read(length)
                    msg = json.loads(payload.decode("utf-8"))
                    if "id" in msg:
                        self.responses[msg["id"]] = msg
                        if msg["id"] in self.response_events:
                            self.response_events[msg["id"]].set()
                    elif "method" in msg:
                        self.notifications.append(msg)
                        self.notifications_event.set()
            except Exception:
                break

    def send_request(self, method, params, timeout=5.0):
        msg_id = str(uuid.uuid4())
        evt = threading.Event()
        self.response_events[msg_id] = evt
        msg = {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params}
        raw = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(raw)}\r\n\r\n".encode("utf-8")
        self.proc.stdin.write(header + raw)
        self.proc.stdin.flush()
        # Block until event is set or timeout
        if evt.wait(timeout):
            ret = self.responses.pop(msg_id, None)
            self.response_events.pop(msg_id, None)
            return ret
        else:
            self.response_events.pop(msg_id, None)
            return None

    def send_notification(self, method, params):
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        raw = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(raw)}\r\n\r\n".encode("utf-8")
        self.proc.stdin.write(header + raw)
        self.proc.stdin.flush()

    def gather_notifications(self, method_filter=None, timeout=10.0):
        self.notifications_event.clear()
        result = []
        start = time.time()
        got_empty_diag = False
        while time.time() - start < timeout:
            for msg in self.notifications[:]:
                if not method_filter or msg.get("method") == method_filter:
                    result.append(msg)
                    self.notifications.remove(msg)
            if result:
                if method_filter == "textDocument/publishDiagnostics":
                    # Return as soon as we see non-empty diagnostics
                    for r in result:
                        params = r.get("params", {})
                        if "diagnostics" in params and params["diagnostics"]:
                            return [r]
                    # Only empty diagnostics so far—wait for a bit longer for LSP server to catch up
                    got_empty_diag = True
                    time.sleep(0.1)
                else:
                    return result
            # Wait for new pub/sub notifications
            self.notifications_event.wait(timeout=timeout - (time.time() - start))
            if got_empty_diag and (time.time() - start) > (timeout - 0.5):
                break  # If we waited most of the timeout after empty, just return
        return result

    def shutdown(self):
        self._running = False
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()
