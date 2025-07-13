import json
import os
import subprocess
import threading
import time
import uuid


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
        """
        Gather notifications from the LSP server.

        For diagnostics, this method collects ALL diagnostic messages.
        This is important because LSP servers
        like gopls often send multiple publishDiagnostics messages:
        - One for compilation errors
        - One for linting issues
        - One for code analysis warnings
        - Separate messages for different files/packages

        The method uses a "settle" strategy: after receiving the first diagnostic
        message, it waits for a brief period (500ms) to collect additional messages
        before returning all collected diagnostics.
        """
        self.notifications_event.clear()
        result = []
        start = time.time()
        last_diagnostic_time = None
        diagnostic_settle_time = 0.5  # Wait 500ms after last diagnostic message

        while time.time() - start < timeout:
            initial_count = len(result)

            # Collect all available notifications matching the filter
            for msg in self.notifications[:]:
                if not method_filter or msg.get("method") == method_filter:
                    result.append(msg)
                    self.notifications.remove(msg)

                    # Track timing for diagnostic messages
                    if method_filter == "textDocument/publishDiagnostics":
                        params = msg.get("params", {})
                        if "diagnostics" in params and params["diagnostics"]:
                            last_diagnostic_time = time.time()

            # Handle diagnostic collection strategy
            if method_filter == "textDocument/publishDiagnostics" and result:
                # If we have diagnostics and enough time has passed since the last one,
                # assume we've collected all available diagnostics
                if (
                    last_diagnostic_time
                    and (time.time() - last_diagnostic_time) >= diagnostic_settle_time
                ):
                    return result

                # If we've been waiting too long (80% of timeout), return what we have
                if (time.time() - start) > (timeout * 0.8):
                    return result

            elif result and method_filter != "textDocument/publishDiagnostics":
                # For non-diagnostic notifications, return immediately
                return result

            # Wait for new notifications or timeout
            remaining_time = timeout - (time.time() - start)
            if remaining_time > 0:
                self.notifications_event.wait(timeout=min(0.1, remaining_time))
            else:
                break

        return result

    def shutdown(self):
        self._running = False
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()
