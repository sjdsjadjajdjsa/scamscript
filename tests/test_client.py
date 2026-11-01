import httpx
import pytest

from scamscript.client import ChatClient, ClientError

MESSAGES = [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "hi"},
]


def make_client(handler, api_key="k"):
    return ChatClient(
        api_key=api_key,
        base_url="https://example.test/v1",
        model="test-model",
        transport=httpx.MockTransport(handler),
    )


def test_complete_returns_content():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={"choices": [{"message": {"content": "hello"}}]})

    with make_client(handler) as client:
        assert client.complete(MESSAGES) == "hello"
    assert seen["auth"] == "Bearer k"
    assert '"test-model"' in seen["body"]
    assert '"stream":false' in seen["body"]


def test_complete_joins_content_parts():
    def handler(request):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": [{"text": "a"}, {"text": "b"}]}}]},
        )

    with make_client(handler) as client:
        assert client.complete(MESSAGES) == "ab"


def test_http_error_includes_body():
    def handler(request):
        return httpx.Response(429, text="slow down")

    with make_client(handler) as client:
        with pytest.raises(ClientError) as excinfo:
            client.complete(MESSAGES)
    assert "429" in str(excinfo.value)
    assert "slow down" in str(excinfo.value)


def test_transport_error_wrapped():
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    with make_client(handler) as client:
        with pytest.raises(ClientError) as excinfo:
            client.complete(MESSAGES)
    assert "boom" in str(excinfo.value)


@pytest.mark.parametrize(
    "body",
    [{}, {"choices": []}, {"choices": [{}]}, {"choices": [{"message": {}}]}, "not json"],
)
def test_bad_shapes_wrapped(body):
    def handler(request):
        if isinstance(body, str):
            return httpx.Response(200, text=body)
        return httpx.Response(200, json=body)

    with make_client(handler) as client:
        with pytest.raises(ClientError):
            client.complete(MESSAGES)


def test_endpoint_strips_trailing_slash():
    with make_client(lambda request: httpx.Response(200, json={})) as client:
        assert client.endpoint == "https://example.test/v1/chat/completions"
