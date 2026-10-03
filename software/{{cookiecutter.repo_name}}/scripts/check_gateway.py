"""Check the running gateway, from the backend's side of its network.

`make smoke-gateway` starts the gateway with gateway/tests/smoke.yaml, which
adds two models that answer "pong" without a network: local/echo and
remote/echo. This checks the key, the visibility policy and the health and
docs endpoints. Each failure prints a line; any failure exits non-zero.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE = "http://gateway:4000"
KEY = os.environ["LITELLM_MASTER_KEY"]


def call(
    path: str, body: dict[str, object] | None = None, key: str | None = KEY
) -> tuple[int, str]:
    """Return the status and body text of one request to the gateway."""
    headers = {"Content-Type": "application/json"}
    if key is not None:
        headers["Authorization"] = f"Bearer {key}"
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(BASE + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def chat(model: str, visibility: str | None) -> tuple[int, str]:
    """Ask a model to answer "ping", stating the content's visibility."""
    body: dict[str, object] = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
    }
    if visibility is not None:
        body["metadata"] = {"visibility": visibility}
    return call("/v1/chat/completions", body)


def main() -> None:
    """Run every check and exit non-zero if any fails."""
    expected = [
        ("health needs no key", call("/health/liveliness", key=None), 200),
        ("no key is refused", call("/v1/models", key=None), 401),
        ("API docs are off", call("/docs", key=None), 404),
        ("the schema is off", call("/openapi.json", key=None), 404),
        ("unknown content to local/", chat("local/echo", None), 200),
        ("unknown content to a remote model", chat("remote/echo", None), 403),
        ("private content to a remote model", chat("remote/echo", "private"),
         403),
        ("public content to a remote model", chat("remote/echo", "public"),
         200),
        ("a misspelt visibility", chat("remote/echo", "publc"), 403),
    ]  # fmt: skip
    problems = [
        f"{name}: HTTP {status}, expected {want}: {text[:200]}"
        for name, (status, text), want in expected
        if status != want
    ]
    for problem in problems:
        print(f"gateway: {problem}", file=sys.stderr)
    if problems:
        sys.exit(1)
    print("gateway: key, health, docs off and the visibility policy")


if __name__ == "__main__":
    main()
