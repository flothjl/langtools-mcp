import subprocess
import json
import threading
import uuid
import os
import time
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    @abstractmethod
    def analyze(self, file_path: str) -> dict:
        pass

class BasicLSPClient:
    def __init__(self, server_cmd):
        self.server_cmd = server_cmd
        self.proc = None
        self.reader_thread = None
        self.responses = {}
        self.notifications = []
        self._buffer = b''
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
                if length_line.lower().startswith(b'content-length:'):
                    length = int(length_line.split(b':')[1].strip())
                    self.proc.stdout.readline()  # blank line
                    payload = self.proc.stdout.read(length)
                    msg = json.loads(payload.decode('utf-8'))
                    if 'id' in msg:
                        self.responses[msg['id']] = msg
                    elif 'method' in msg:
                        self.notifications.append(msg)
            except Exception:
                break

    def send_request(self, method, params):
        msg_id = str(uuid.uuid4())
        msg = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params
        }
        raw = json.dumps(msg).encode('utf-8')
        header = f"Content-Length: {len(raw)}\r\n\r\n".encode('utf-8')
        self.proc.stdin.write(header + raw)
        self.proc.stdin.flush()
        for _ in range(100):
            if msg_id in self.responses:
                return self.responses.pop(msg_id)
            time.sleep(0.1)
        return None

    def send_notification(self, method, params):
        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        raw = json.dumps(msg).encode('utf-8')
        header = f"Content-Length: {len(raw)}\r\n\r\n".encode('utf-8')
        self.proc.stdin.write(header + raw)
        self.proc.stdin.flush()

    def gather_notifications(self, method_filter=None, timeout=2.0):
        t0 = time.time()
        res = []
        while time.time() - t0 < timeout:
            time.sleep(0.1)
            for msg in self.notifications[:]:
                if not method_filter or msg.get('method') == method_filter:
                    res.append(msg)
                    self.notifications.remove(msg)
        return res

    def shutdown(self):
        self._running = False
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()

class GoplsLSPAdapter(BaseAdapter):
    def __init__(self, gopls_path="gopls"):
        self.lsp = BasicLSPClient([gopls_path, "serve", "--listen", "stdio"])

    def analyze(self, file_path):
        self.lsp.start()
        with open(file_path) as f:
            file_content = f.read()
        root_uri = "file://" + os.path.dirname(os.path.abspath(file_path))
        self.lsp.send_request("initialize", {"rootUri": root_uri, "capabilities": {}, "processId": None})
        self.lsp.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": f"file://{os.path.abspath(file_path)}",
                "languageId": "go",
                "version": 1,
                "text": file_content
            }
        })
        diags = self.lsp.gather_notifications("textDocument/publishDiagnostics", timeout=2.0)
        self.lsp.shutdown()
        if not diags:
            return {"status": "ok", "note": "No diagnostics received."}
        return {"status": "ok", "diagnostics": diags}
