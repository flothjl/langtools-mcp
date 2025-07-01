import json
import http.client

class LSPDaemonClient:
    def __init__(self, host="localhost", port=61782):
        self.host = host
        self.port = port

    def analyze(self, file_path, language):
        conn = http.client.HTTPConnection(self.host, self.port, timeout=60)
        data = json.dumps({"file_path": file_path, "language": language})
        conn.request("POST", "/", body=data, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        resp_data = resp.read()
        return json.loads(resp_data)
