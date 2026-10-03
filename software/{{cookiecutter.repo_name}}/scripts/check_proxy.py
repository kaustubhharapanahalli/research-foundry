"""Check the running proxy from inside its network namespace.

`make smoke-proxy` runs this in the backend image, sharing the proxy
container's network and its /data volume, so https://localhost:8443 is the
proxy itself and its local certificate authority signs what it serves.
Each failed check prints one line; any failure exits non-zero.
"""

import http.client
import json
import socket
import ssl
import sys
import warnings

CA = "/data/caddy/pki/authorities/local/root.crt"
HOST = "localhost"
FRONTEND = {{ "True" if cookiecutter.frontend_nextjs == "yes" else "False" }}


def request(
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    tls: bool = True,
) -> http.client.HTTPResponse:
    """Send one request to the proxy and return the response."""
    connection: http.client.HTTPConnection
    if tls:
        context = ssl.create_default_context(cafile=CA)
        connection = http.client.HTTPSConnection(
            HOST, 8443, context=context, timeout=10
        )
    else:
        connection = http.client.HTTPConnection(HOST, 8080, timeout=10)
    connection.request(
        method, path, body=body, headers={"Host": HOST, **(headers or {})}
    )
    return connection.getresponse()


SITE_HEADERS = (
    "strict-transport-security",
    "permissions-policy",
    "cross-origin-opener-policy",
    "cross-origin-resource-policy",
)


def check_headers() -> list[str]:
    """The site's headers are set once each, and Caddy does not name itself.

    Django sets HSTS and COOP too, and Next.js sets Permissions-Policy; the
    proxy's copy replaces theirs, so each arrives exactly once.
    """
    response = request("GET", "/health/")
    problems = []
    if response.status != 200 or json.load(response) != {"status": "ok"}:
        problems.append(f"/health/ through the proxy: HTTP {response.status}")
    responses = {"/health/": response.getheaders()}
    if FRONTEND:
        page = request("GET", "/")
        page.read()
        responses["/"] = page.getheaders()
    for path, received in responses.items():
        names = [name.lower() for name, _ in received]
        problems += [
            f"{path}: {names.count(name)} {name} headers, not 1"
            for name in SITE_HEADERS
            if names.count(name) != 1
        ]
        problems += [
            f"{path}: the {name} header leaks"
            for name in ("server", "via")
            if name in names
        ]
    return problems


def handshake(version: ssl.TLSVersion) -> str:
    """Return the TLS version agreed, or the reason the handshake failed."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(CA)
    # Let the client offer old versions, so any refusal is the server's.
    context.set_ciphers("DEFAULT:@SECLEVEL=0")
    context.minimum_version = context.maximum_version = version
    try:
        with socket.create_connection((HOST, 8443), timeout=10) as raw:
            with context.wrap_socket(raw, server_hostname=HOST) as tls:
                return tls.version() or ""
    except ssl.SSLError as error:
        return str(error.reason)


def check_tls_versions() -> list[str]:
    """TLS 1.2 and 1.3 are served; the server itself refuses TLS 1.1."""
    problems = [
        f"{name} was not served: {agreed}"
        for version, name in (
            (ssl.TLSVersion.TLSv1_2, "TLSv1.2"),
            (ssl.TLSVersion.TLSv1_3, "TLSv1.3"),
        )
        if (agreed := handshake(version)) != name
    ]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        old = handshake(ssl.TLSVersion.TLSv1_1)
    # The alert comes from the server; a client-side refusal would not
    # show that the proxy refuses it.
    if old != "TLSV1_ALERT_PROTOCOL_VERSION":
        problems.append(f"TLSv1.1 was not refused by the proxy: {old}")
    return problems


def check_forwarding() -> list[str]:
    """A client's X-Forwarded-Proto is replaced, not trusted.

    Django trusts the proxy's X-Forwarded-Proto. Were a client's "http"
    passed on, Django would redirect this HTTPS request to HTTPS.
    """
    response = request("GET", "/health/", {"X-Forwarded-Proto": "http"})
    response.read()
    if response.status != 200:
        return [f"a spoofed X-Forwarded-Proto got HTTP {response.status}"]
    return []


def check_page() -> list[str]:
    """The frontend's page arrives through the proxy, backend up."""
    if not FRONTEND:
        return []
    response = request("GET", "/")
    if response.status != 200 or "Backend: up" not in response.read().decode():
        return [f"the page through the proxy: HTTP {response.status}"]
    return []


def check_redirect() -> list[str]:
    """Plain HTTP is redirected to HTTPS."""
    response = request("GET", "/health/", tls=False)
    response.read()
    location = response.getheader("Location", "")
    if response.status != 308 or not location.startswith("https://"):
        return [f"plain HTTP was not redirected: HTTP {response.status}"]
    return []


def check_unknown_hosts() -> list[str]:
    """A request for any other host name is closed unanswered."""
    problems = []
    for tls in (True, False):
        try:
            request("GET", "/", {"Host": "unknown.example"}, tls=tls)
        except (ConnectionError, http.client.HTTPException, ssl.SSLError):
            continue
        scheme = "HTTPS" if tls else "HTTP"
        problems.append(f"an {scheme} request for an unknown host answered")
    return problems


def main() -> None:
    """Run every check and exit non-zero if any fails."""
    problems = [
        *check_tls_versions(),
        *check_headers(),
        *check_forwarding(),
        *check_page(),
        *check_redirect(),
        *check_unknown_hosts(),
    ]
    for problem in problems:
        print(f"proxy: {problem}", file=sys.stderr)
    if problems:
        sys.exit(1)
    print(
        "proxy: TLS 1.2 and 1.3 only, headers once each, forwarding, "
        "redirect and unknown hosts"
    )


if __name__ == "__main__":
    main()
