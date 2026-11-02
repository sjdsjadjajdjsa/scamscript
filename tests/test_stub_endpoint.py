import importlib.util
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("stub_endpoint", ROOT / "scripts" / "stub_endpoint.py")
stub = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(stub)


def serve(responses):
    stub.StubHandler.responses = responses
    server = ThreadingHTTPServer(("127.0.0.1", 0), stub.StubHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def post(server, prompt):
    request = urllib.request.Request(
        f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
        data=json.dumps({"messages": [{"role": "user", "content": prompt}]}).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())


def parse(body):
    return json.loads(body["choices"][0]["message"]["content"])


def test_matches_on_filename():
    server = serve({"alpha.txt": {"attack_type": "alpha"}, "beta.txt": {"attack_type": "beta"}})
    try:
        assert parse(post(server, "Artifact: beta.txt")) == {"attack_type": "beta"}
    finally:
        server.shutdown()
        server.server_close()


def test_falls_back_to_first_reply():
    server = serve({"alpha.txt": {"attack_type": "alpha"}})
    try:
        assert parse(post(server, "Artifact: unknown.txt")) == {"attack_type": "alpha"}
    finally:
        server.shutdown()
        server.server_close()


def test_response_carries_finish_reason_and_cost():
    server = serve({"alpha.txt": {"attack_type": "alpha"}})
    try:
        body = post(server, "Artifact: alpha.txt")
        assert body["choices"][0]["finish_reason"] == "stop"
        assert body["usage"]["cost"] == stub.COST_PER_REPLY
    finally:
        server.shutdown()
        server.server_close()


def test_default_responses_load():
    payload = json.loads(stub.DEFAULT_RESPONSES.read_text(encoding="utf-8"))
    assert "tech_support_scam.txt" in payload
