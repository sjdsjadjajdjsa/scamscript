import json
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
        retries=0,
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


def test_retries_retryable_status_then_succeeds():
    calls = []
    slept = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503, text="starting up", headers={"retry-after": "0.5"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = ChatClient(
        api_key="k",
        base_url="https://example.test/v1",
        retries=2,
        transport=httpx.MockTransport(handler),
        sleep=slept.append,
    )
    with client:
        assert client.complete(MESSAGES) == "ok"
    assert len(calls) == 2
    assert slept == [0.5]


def test_gives_up_after_retries():
    def handler(request):
        return httpx.Response(502, text="bad gateway")

    client = ChatClient(
        api_key="k",
        base_url="https://example.test/v1",
        retries=1,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    with client:
        with pytest.raises(ClientError, match="502"):
            client.complete(MESSAGES)


def test_4xx_not_retried():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(401, text="bad key")

    client = ChatClient(
        api_key="k",
        base_url="https://example.test/v1",
        retries=3,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    with client:
        with pytest.raises(ClientError, match="401"):
            client.complete(MESSAGES)
    assert len(calls) == 1


def test_truncation_raises_with_partial():
    from scamscript.client import TruncatedError

    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"attack_type": "vish'}, "finish_reason": "length"}
                ]
            },
        )

    with make_client(handler) as client:
        with pytest.raises(TruncatedError) as excinfo:
            client.complete(MESSAGES)
    assert excinfo.value.partial == '{"attack_type": "vish'


def test_truncation_not_retried():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "x"}, "finish_reason": "length"}]},
        )

    client = ChatClient(
        api_key="k",
        base_url="https://example.test/v1",
        retries=3,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    with client:
        with pytest.raises(ClientError):
            client.complete(MESSAGES)
    assert len(calls) == 1


def test_max_tokens_default_sent():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.read()))
        return httpx.Response(200, json={"choices": [{"message": {"content": "a"}}]})

    client = ChatClient(
        api_key="k",
        base_url="https://example.test/v1",
        max_tokens=1234,
        transport=httpx.MockTransport(handler),
    )
    with client:
        client.complete(MESSAGES)
    assert seen["max_tokens"] == 1234


def test_empty_content_retried():
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(
                200, json={"choices": [{"message": {"content": None}, "finish_reason": "stop"}]}
            )
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = ChatClient(
        api_key="k",
        base_url="https://example.test/v1",
        retries=1,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    with client:
        assert client.complete(MESSAGES) == "ok"
    assert len(calls) == 2


def test_usage_captured():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "a"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 4, "cost": 0.5},
            },
        )

    with make_client(handler) as client:
        client.complete(MESSAGES)
        assert client.last_usage == {"prompt_tokens": 3, "completion_tokens": 4, "cost": 0.5}


def test_reasoning_used_when_content_empty():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": None, "reasoning": '{"attack_type": "x"}'}, "finish_reason": "stop"}
                ]
            },
        )

    with make_client(handler) as client:
        assert client.complete(MESSAGES) == '{"attack_type": "x"}'


def test_length_with_only_reasoning_is_truncation():
    from scamscript.client import TruncatedError

    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": None, "reasoning": "thinking..."}, "finish_reason": "length"}
                ]
            },
        )

    with make_client(handler) as client:
        with pytest.raises(TruncatedError) as excinfo:
            client.complete(MESSAGES)
    assert excinfo.value.partial == "thinking..."
