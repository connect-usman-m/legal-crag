import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.core.config import Settings
from app.graph.nodes.web_correct import search_web

PAYLOAD = {
    "results": [
        {
            "url": "https://oag.ca.gov/privacy/ccpa",
            "title": "CCPA penalties",
            "content": "Civil penalties per violation",
            "score": 0.8,
        }
    ]
}


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        body = json.dumps(PAYLOAD).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def test_search_web_uses_tavily_and_maps_results(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(
        "app.graph.nodes.web_correct.rerank_web_results",
        lambda _query, results, _model: results,
    )
    settings = Settings(_env_file=None, groq_api_key="x", tavily_api_key="test-key")
    try:
        results = search_web(
            "CCPA penalties",
            settings,
            base_url=f"http://127.0.0.1:{server.server_port}",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert results[0].domain == "oag.ca.gov"
    assert results[0].content == "Civil penalties per violation"
