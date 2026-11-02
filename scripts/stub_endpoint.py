#!/usr/bin/env python
"""Serve recorded breakdowns to the CLI so samples can be rebuilt offline.

Responses are keyed by a filename that appears in the prompt. This is a
development aid, not a model: every reply is replayed verbatim.

Usage:
    python scripts/stub_endpoint.py --port 8791
    SCAMSCRIPT_BASE_URL=http://127.0.0.1:8791/v1 scamscript batch examples
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_RESPONSES = Path(__file__).with_name("sample_responses.json")
DEFAULT_PORT = 8791
COST_PER_REPLY = 0.0002


class StubHandler(BaseHTTPRequestHandler):
    responses: dict[str, dict] = {}

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            body = {}
        messages = body.get("messages") or [{}]
        prompt = messages[-1].get("content", "")
        payload = next(
            (reply for name, reply in self.responses.items() if name in prompt),
            next(iter(self.responses.values()), {}),
        )
        raw = json.dumps(
            {
                "choices": [
                    {
                        "message": {"content": json.dumps(payload)},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200, "cost": COST_PER_REPLY},
            }
        ).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args: object) -> None:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses", type=Path, default=DEFAULT_RESPONSES)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    StubHandler.responses = json.loads(args.responses.read_text(encoding="utf-8"))
    server = ThreadingHTTPServer((args.host, args.port), StubHandler)
    print(f"serving {len(StubHandler.responses)} recorded replies on "
          f"http://{args.host}:{args.port}/v1", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
