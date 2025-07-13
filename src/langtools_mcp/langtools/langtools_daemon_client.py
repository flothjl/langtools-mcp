import http.client
import json

SUPPORTED_LANGUAGES = ["go", "python"]


class LangtoolsDaemonClient:
    def __init__(self, host="localhost", port=61782):
        self.host = host
        self.port = port

    def validate_language(self, language: str):
        if language not in SUPPORTED_LANGUAGES:
            raise NotImplementedError(
                f"No analyzer registered for language: {language!r}"
            )

    def analyze(self, language: str, project_root: str):
        self.validate_language(language)
        conn = http.client.HTTPConnection(self.host, self.port, timeout=60)
        data = json.dumps({"language": language, "project_root": project_root})
        conn.request(
            "POST", "/", body=data, headers={"Content-Type": "application/json"}
        )
        resp = conn.getresponse()
        resp_data = resp.read()
        return json.loads(resp_data)
