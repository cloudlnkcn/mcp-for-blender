"""The HTTP/SSE transports: how the server picks one and whether it serves.

The config half follows the same contract test_connection_args.py pins for the
Blender address -- CLI flags > environment > defaults, tolerant of unknown
client-appended args -- and adds one deliberate break from it: an explicitly
configured but unknown transport is fatal, because a silent stdio fallback
looks to an HTTP client like a hang, not a misconfiguration.

The middle half covers the dispatch and wiring layers (main()'s stdio/http
split, _run_http_transport's settings choreography) with fakes, because the
ordering there -- settings assigned before the app is built -- is exactly what
the streamable transport snapshots and what no app-level test would catch.

The integration half boots the real ASGI app under uvicorn in a background
thread and drives it with the SDK's own clients, since the transports are
where subtle lifespan/session bugs would live and mocks would not catch them.
"""

import asyncio
import socket
import sys
import threading
import time

import pytest

from blender_mcp import server as server_module
from blender_mcp.server import (
    DEFAULT_HTTP_HOST,
    DEFAULT_HTTP_PORT,
    mcp,
    parse_server_args,
    resolve_http_listener,
    resolve_stateless_http,
    resolve_transport,
)


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """Never inherit real transport config from the developer's shell."""
    monkeypatch.delenv("BLENDER_MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("BLENDER_MCP_HTTP_HOST", raising=False)
    monkeypatch.delenv("BLENDER_MCP_HTTP_PORT", raising=False)
    monkeypatch.delenv("BLENDER_MCP_HTTP_STATELESS", raising=False)
    monkeypatch.delenv("BLENDER_MCP_HTTP_TOKEN", raising=False)
    monkeypatch.setenv("DISABLE_TELEMETRY", "1")


@pytest.fixture(autouse=True)
def _no_blender(monkeypatch):
    """Keep the integration servers from talking to a real Blender addon if
    one happens to be listening on this machine; the lifespan's guarded
    connect attempt turns into the ordinary not-running warning instead."""
    def _refuse(*_args, **_kwargs):
        raise RuntimeError("tests run without a Blender addon")

    monkeypatch.setattr(server_module, "get_blender_connection", _refuse)


@pytest.fixture(autouse=True)
def _restore_settings(monkeypatch):
    """_run_http_transport mutates module-global FastMCP settings; pin them so
    every test starts from the same defaults and later tests (which build real
    apps from the same server object) don't inherit a previous test's posture."""
    monkeypatch.setattr(mcp.settings, "host", mcp.settings.host)
    monkeypatch.setattr(mcp.settings, "port", mcp.settings.port)
    monkeypatch.setattr(mcp.settings, "stateless_http", mcp.settings.stateless_http)
    monkeypatch.setattr(mcp.settings, "transport_security", mcp.settings.transport_security)


# --- transport selection ---------------------------------------------------


def test_transport_defaults_to_stdio():
    assert resolve_transport() == "stdio"


def test_empty_transport_env_is_unset(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_TRANSPORT", "")
    assert resolve_transport() == "stdio"


def test_whitespace_transport_env_is_unset(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_TRANSPORT", "   ")
    assert resolve_transport() == "stdio"


@pytest.mark.parametrize("raw", ["http", "streamable-http", "streamable_http", "HTTP", " Streamable-HTTP "])
def test_streamable_http_aliases_normalize(raw):
    assert resolve_transport(raw) == "streamable-http"


def test_sse_transport_is_accepted():
    assert resolve_transport("sse") == "sse"


def test_transport_env_used_when_no_cli_flag(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_TRANSPORT", "sse")
    assert resolve_transport() == "sse"


def test_transport_cli_flag_beats_environment(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_TRANSPORT", "sse")
    assert resolve_transport("http") == "streamable-http"


def test_unknown_transport_is_fatal():
    # A silent stdio fallback would leave an HTTP client staring at a dead
    # URL; failing at startup names the problem instead.
    with pytest.raises(SystemExit, match="Unknown transport 'ws'"):
        resolve_transport("ws")


def test_unknown_transport_error_names_the_aliases():
    with pytest.raises(SystemExit, match="streamable-http"):
        resolve_transport("bogus")


# --- HTTP listener address --------------------------------------------------


def test_http_listener_defaults():
    assert resolve_http_listener() == (DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT)


def test_http_listener_environment_overrides_defaults(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_HTTP_HOST", "0.0.0.0")
    monkeypatch.setenv("BLENDER_MCP_HTTP_PORT", "9000")
    assert resolve_http_listener() == ("0.0.0.0", 9000)


def test_http_listener_blank_env_host_falls_back_to_loopback(monkeypatch):
    # An env var present but blank must not silently become "bind all
    # interfaces"; that would defeat the loopback-by-default posture.
    monkeypatch.setenv("BLENDER_MCP_HTTP_HOST", "")
    assert resolve_http_listener() == (DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT)

    monkeypatch.setenv("BLENDER_MCP_HTTP_HOST", "   ")
    assert resolve_http_listener() == (DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT)


def test_http_listener_cli_overrides_environment(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_HTTP_HOST", "0.0.0.0")
    monkeypatch.setenv("BLENDER_MCP_HTTP_PORT", "9000")
    assert resolve_http_listener("127.0.0.1", 8001) == ("127.0.0.1", 8001)


def test_http_listener_cli_host_and_port_override_independently(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_HTTP_HOST", "0.0.0.0")
    monkeypatch.setenv("BLENDER_MCP_HTTP_PORT", "9000")
    assert resolve_http_listener(cli_port=8001) == ("0.0.0.0", 8001)
    assert resolve_http_listener(cli_host="127.0.0.1") == ("127.0.0.1", 9000)


def test_http_listener_unparseable_env_port_falls_back(monkeypatch):
    # Mirrors the BLENDER_PORT contract: a bad value warns and falls back
    # rather than raising from inside startup.
    monkeypatch.setenv("BLENDER_MCP_HTTP_PORT", "not-a-port")
    assert resolve_http_listener() == (DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT)


def test_http_listener_unparseable_env_port_warns(monkeypatch, caplog):
    monkeypatch.setenv("BLENDER_MCP_HTTP_PORT", "not-a-port")
    with caplog.at_level("WARNING"):
        resolve_http_listener()
    assert "not a valid port number" in caplog.text


@pytest.mark.parametrize("bad", ["-1", "70000", "65536"])
def test_http_listener_out_of_range_env_port_falls_back(monkeypatch, bad, caplog):
    monkeypatch.setenv("BLENDER_MCP_HTTP_PORT", bad)
    with caplog.at_level("WARNING"):
        assert resolve_http_listener() == (DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT)
    assert "out of range" in caplog.text


@pytest.mark.parametrize("bad", [-1, 70000])
def test_http_listener_out_of_range_cli_port_is_fatal(bad):
    # A CLI flag is an explicit ask; a silent fallback would bind somewhere
    # the user did not choose.
    with pytest.raises(SystemExit, match="Invalid --http-port"):
        resolve_http_listener(cli_port=bad)


def test_http_listener_port_zero_from_cli_is_respected(monkeypatch):
    # The integration tests below rely on this for ephemeral ports.
    monkeypatch.setenv("BLENDER_MCP_HTTP_PORT", "9000")
    assert resolve_http_listener(cli_port=0) == (DEFAULT_HTTP_HOST, 0)


# --- stateless mode ----------------------------------------------------------


def test_stateless_defaults_to_off():
    assert resolve_stateless_http() is False


def test_stateless_cli_flag_wins():
    assert resolve_stateless_http(cli_flag=True) is True


@pytest.mark.parametrize("raw", ["1", "true", "True", "YES", "on"])
def test_stateless_env_truthy_values(monkeypatch, raw):
    monkeypatch.setenv("BLENDER_MCP_HTTP_STATELESS", raw)
    assert resolve_stateless_http() is True


@pytest.mark.parametrize("raw", ["0", "false", "False", "no", "off", "", "falso"])
def test_stateless_env_falsy_values(monkeypatch, raw):
    # "falso" pins the behavior for unrecognized junk: not an error, just off.
    monkeypatch.setenv("BLENDER_MCP_HTTP_STATELESS", raw)
    assert resolve_stateless_http() is False


# --- argv parsing -------------------------------------------------------------


def test_parses_all_transport_flags():
    args = parse_server_args(
        ["--transport", "http", "--http-host", "0.0.0.0", "--http-port", "9000", "--stateless-http"]
    )
    assert args.transport == "http"
    assert args.http_host == "0.0.0.0"
    assert args.http_port == 9000
    assert args.stateless_http is True


def test_no_transport_flags_yields_no_overrides():
    args = parse_server_args([])
    assert args.transport is None
    assert args.http_host is None
    assert args.http_port is None
    assert args.stateless_http is False


def test_unknown_args_still_ignored_alongside_transport_flags():
    # Client-appended args must not abort startup even when the user also
    # passes transport flags.
    args = parse_server_args(["--some-client-flag", "--transport", "http", "--http-port", "9000"])
    assert args.transport == "http"
    assert args.http_port == 9000


def test_client_args_are_never_mistaken_for_abbreviations():
    # With argparse's default prefix matching, a client's unrelated `--state`
    # would be silently swallowed as --stateless-http and flip the session
    # semantics, and `--h` would hard-crash as ambiguous. Prefix matching is
    # off, so both land in the ordinary unknown-args warning path.
    args = parse_server_args(["--state", "x"])
    assert args.stateless_http is False

    args = parse_server_args(["--h", "localhost"])
    assert args.host is None
    assert args.http_host is None


# --- bearer token ---------------------------------------------------------------


def test_token_unset_means_no_auth(monkeypatch):
    assert server_module._resolve_http_token() is None


def test_blank_token_is_a_config_error(monkeypatch):
    # "  " reads like "auth enabled, value lost" -- failing loudly beats
    # silently serving an unauthenticated endpoint.
    monkeypatch.setenv("BLENDER_MCP_HTTP_TOKEN", "   ")
    with pytest.raises(SystemExit, match="blank"):
        server_module._resolve_http_token()


def test_non_ascii_token_is_a_config_error(monkeypatch):
    # HTTP header values cap out at latin-1; better to name that at startup
    # than die with a raw UnicodeEncodeError from inside the middleware.
    monkeypatch.setenv("BLENDER_MCP_HTTP_TOKEN", "秘密")
    with pytest.raises(SystemExit, match="printable ASCII"):
        server_module._resolve_http_token()


def test_control_char_token_is_a_config_error(monkeypatch):
    # A pasted newline would make every request 401 forever.
    monkeypatch.setenv("BLENDER_MCP_HTTP_TOKEN", "tok\nnl")
    with pytest.raises(SystemExit, match="printable ASCII"):
        server_module._resolve_http_token()


def test_padded_token_is_trimmed(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_HTTP_TOKEN", "  sekrit  ")
    assert server_module._resolve_http_token() == "sekrit"


def test_transport_security_follows_bind_address():
    loopback = server_module._transport_security_for("127.0.0.1")
    assert loopback.enable_dns_rebinding_protection is True
    assert "127.0.0.1:*" in loopback.allowed_hosts

    # Explicit, not inherited from the SDK's construction-time default, which
    # would keep the loopback allowlist and 421 every remote client.
    wide = server_module._transport_security_for("0.0.0.0")
    assert wide.enable_dns_rebinding_protection is False

    assert server_module._transport_security_for("192.168.1.5").enable_dns_rebinding_protection is False
    assert server_module._transport_security_for("localhost").enable_dns_rebinding_protection is True


@pytest.mark.parametrize("host", ["127.0.0.2", "LocalHost", "[::1]", "::1", "localhost"])
def test_loopback_detection_covers_the_whole_family(host):
    # 127.0.0.0/8 is loopback, not just 127.0.0.1; case and brackets must not
    # flip the security posture to fail-open.
    assert server_module._is_loopback_listen_host(host) is True


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.5", "blender.example.com", ""])
def test_non_loopback_detection(host):
    assert server_module._is_loopback_listen_host(host) is False


# --- main() dispatch -------------------------------------------------------------


def _patch_uvicorn(monkeypatch):
    calls = {}

    def fake_run(app, host, port, log_level):
        calls.update(app=app, host=host, port=port, log_level=log_level)

    monkeypatch.setattr("uvicorn.run", fake_run)
    return calls


def _run_main(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["mcp-for-blender", *argv])


def test_main_defaults_to_stdio(monkeypatch):
    _run_main(monkeypatch, [])
    ran = []
    monkeypatch.setattr(mcp, "run", lambda: ran.append("stdio"))
    monkeypatch.setattr(
        server_module, "_run_http_transport",
        lambda *a: ran.append(("http", *a)),
    )
    server_module.main()
    assert ran == ["stdio"]


def test_main_dispatches_http_transport(monkeypatch):
    _run_main(monkeypatch, ["--transport", "http", "--http-host", "0.0.0.0", "--http-port", "9000", "--stateless-http"])
    seen = []
    monkeypatch.setattr(mcp, "run", lambda: seen.append("stdio"))
    monkeypatch.setattr(server_module, "_run_http_transport", lambda *a: seen.append(a))
    server_module.main()
    assert seen == [("streamable-http", "0.0.0.0", 9000, True)]


def test_main_dispatches_sse_transport(monkeypatch):
    _run_main(monkeypatch, ["--transport", "sse"])
    seen = []
    monkeypatch.setattr(mcp, "run", lambda: seen.append("stdio"))
    monkeypatch.setattr(server_module, "_run_http_transport", lambda *a: seen.append(a))
    server_module.main()
    assert seen == [("sse", DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT, False)]


def test_main_invalid_transport_exits_before_serving(monkeypatch):
    _run_main(monkeypatch, ["--transport", "bogus"])
    seen = []
    monkeypatch.setattr(mcp, "run", lambda: seen.append("stdio"))
    monkeypatch.setattr(server_module, "_run_http_transport", lambda *a: seen.append(a))
    with pytest.raises(SystemExit, match="Unknown transport"):
        server_module.main()
    assert seen == []


def test_main_records_blender_address_globals(monkeypatch):
    # Tools resolve the Blender address through these globals; the HTTP path
    # must keep feeding them from --host/--port exactly like stdio does.
    # monkeypatch pins their current values so main()'s reassignment is undone.
    monkeypatch.setattr(server_module, "CLI_HOST", None)
    monkeypatch.setattr(server_module, "CLI_PORT", None)
    _run_main(monkeypatch, ["--host", "10.0.0.5", "--port", "9877", "--transport", "http"])
    monkeypatch.setattr(mcp, "run", lambda: None)
    monkeypatch.setattr(server_module, "_run_http_transport", lambda *a: None)
    server_module.main()
    assert server_module.CLI_HOST == "10.0.0.5"
    assert server_module.CLI_PORT == 9877


# --- _run_http_transport wiring ----------------------------------------------------


def test_run_http_applies_settings_before_building_the_app(monkeypatch):
    # The streamable transport snapshots stateless_http and the Host/Origin
    # rules when the app is built, so the assignments must happen first --
    # observe both from inside the build.
    seen_at_build = {}
    real_app_builder = mcp.streamable_http_app

    def build_and_record():
        seen_at_build["stateless"] = mcp.settings.stateless_http
        seen_at_build["security"] = mcp.settings.transport_security
        return real_app_builder()

    monkeypatch.setattr(mcp, "streamable_http_app", build_and_record)
    calls = _patch_uvicorn(monkeypatch)

    server_module._run_http_transport("streamable-http", "127.0.0.1", 8765, True)

    assert seen_at_build["stateless"] is True
    assert seen_at_build["security"].enable_dns_rebinding_protection is True
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 8765


def test_run_http_loopback_keeps_dns_rebinding_protection(monkeypatch):
    _patch_uvicorn(monkeypatch)
    server_module._run_http_transport("streamable-http", "127.0.0.1", 8765, False)
    assert mcp.settings.transport_security.enable_dns_rebinding_protection is True


def test_run_http_wide_bind_without_token_warns_and_unlocks_host_checks(monkeypatch, caplog):
    _patch_uvicorn(monkeypatch)
    with caplog.at_level("WARNING"):
        server_module._run_http_transport("streamable-http", "0.0.0.0", 8765, False)
    assert mcp.settings.transport_security.enable_dns_rebinding_protection is False
    assert "without a bearer token" in caplog.text


def test_run_http_wide_bind_with_token_does_not_warn(monkeypatch, caplog):
    monkeypatch.setenv("BLENDER_MCP_HTTP_TOKEN", "sekrit")
    _patch_uvicorn(monkeypatch)
    with caplog.at_level("WARNING"):
        server_module._run_http_transport("streamable-http", "0.0.0.0", 8765, False)
    assert "without a bearer token" not in caplog.text


def test_run_http_wraps_app_in_bearer_middleware(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_HTTP_TOKEN", "sekrit")
    calls = _patch_uvicorn(monkeypatch)
    wrapped = []

    real_middleware = server_module._bearer_auth_middleware
    sentinel = object()

    def spy(app, token):
        wrapped.append(token)
        return sentinel

    monkeypatch.setattr(server_module, "_bearer_auth_middleware", spy)
    server_module._run_http_transport("streamable-http", "127.0.0.1", 8765, False)

    assert wrapped == ["sekrit"]
    assert calls["app"] is sentinel


def test_run_http_sse_endpoint_and_stateless_warning(monkeypatch, caplog):
    calls = _patch_uvicorn(monkeypatch)
    with caplog.at_level("WARNING"):
        server_module._run_http_transport("sse", "127.0.0.1", 8765, True)
    assert calls["port"] == 8765
    assert "no effect on the sse transport" in caplog.text
    # sse ignores stateless: the setting must stay untouched for sse binds.
    assert mcp.settings.stateless_http is False


def test_run_http_blank_token_is_fatal(monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_HTTP_TOKEN", "   ")
    _patch_uvicorn(monkeypatch)
    with pytest.raises(SystemExit, match="blank"):
        server_module._run_http_transport("streamable-http", "127.0.0.1", 8765, False)


# --- integration: serve real MCP over HTTP -------------------------------------


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((DEFAULT_HTTP_HOST, 0))
        return sock.getsockname()[1]


def _serve(build_app, port):
    """Reset per-server globals, build the app, run it under uvicorn in a
    daemon thread. `build_app` is a zero-arg callable so the app (and any
    state it captures) is created *after* the resets."""

    # Both resets below only matter because these tests boot several servers
    # in one process; production starts exactly one server per process.
    try:
        # sse-starlette caches a module-global asyncio.Event that gets bound
        # to whichever server's loop used it first; a later server in the
        # same process then hits "bound to a different event loop" and its
        # SSE streams die. Drop it so each server gets a fresh event.
        from sse_starlette.sse import AppStatus

        AppStatus.should_exit_event = None
    except ImportError:
        pass
    # FastMCP caches its StreamableHTTPSessionManager on first use and the
    # manager refuses a second lifespan run, so a second streamable app in
    # the same process would fail startup. Drop the cache.
    mcp._session_manager = None

    app = build_app()
    import uvicorn

    config = uvicorn.Config(app, host=DEFAULT_HTTP_HOST, port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if server.started:
            return server, thread
        if not thread.is_alive():
            raise RuntimeError("uvicorn thread exited before becoming ready")
        time.sleep(0.05)
    server.should_exit = True
    thread.join(timeout=5)
    raise TimeoutError("uvicorn did not start within 15s")


def _stop(server, thread):
    server.should_exit = True
    thread.join(timeout=5)
    # give the port a beat to release even if the thread is wedged
    time.sleep(0.2)


# The deprecated spelling is kept deliberately: the renamed replacement does
# not accept custom headers, which the bearer tests need to authenticate with.
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client  # noqa: E402


async def _list_tools_over_streamable_http(url, headers=None):
    from mcp import ClientSession

    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return sorted(tool.name for tool in result.tools)


async def _list_tools_over_sse(url, headers=None):
    from mcp import ClientSession

    async with sse_client(url, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return sorted(tool.name for tool in result.tools)


def _run_client_flow(flow, *args):
    # Bound the flow so a broken server surfaces as a timeout failure
    # instead of a hang that stalls the whole suite.
    return asyncio.run(asyncio.wait_for(flow(*args), timeout=30))


def test_streamable_http_serves_tools():
    pytest.importorskip("uvicorn")
    port = _free_port()
    server, thread = _serve(mcp.streamable_http_app, port)
    try:
        names = _run_client_flow(_list_tools_over_streamable_http, f"http://{DEFAULT_HTTP_HOST}:{port}/mcp")
    finally:
        _stop(server, thread)
    # get_scene_info is a plain tool every client should see; the app-only
    # viewport tools are filtered per-client and asserted nowhere here.
    assert "get_scene_info" in names
    assert "execute_blender_code" in names


def test_sse_serves_tools():
    pytest.importorskip("uvicorn")
    port = _free_port()
    server, thread = _serve(mcp.sse_app, port)
    try:
        names = _run_client_flow(_list_tools_over_sse, f"http://{DEFAULT_HTTP_HOST}:{port}/sse")
    finally:
        _stop(server, thread)
    assert "get_scene_info" in names
    assert "execute_blender_code" in names


def test_bearer_token_rejects_unsigned_requests():
    pytest.importorskip("uvicorn")
    import urllib.error
    import urllib.request

    port = _free_port()
    server, thread = _serve(
        lambda: server_module._bearer_auth_middleware(mcp.streamable_http_app(), "sekrit"), port
    )
    try:
        base = f"http://{DEFAULT_HTTP_HOST}:{port}/mcp"
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(base, timeout=5)
        assert exc_info.value.code == 401
    finally:
        _stop(server, thread)


def test_bearer_token_admits_full_session_over_streamable_http():
    pytest.importorskip("uvicorn")
    port = _free_port()
    server, thread = _serve(
        lambda: server_module._bearer_auth_middleware(mcp.streamable_http_app(), "sekrit"), port
    )
    try:
        names = _run_client_flow(
            _list_tools_over_streamable_http,
            f"http://{DEFAULT_HTTP_HOST}:{port}/mcp",
            {"Authorization": "Bearer sekrit"},
        )
    finally:
        _stop(server, thread)
    # A real initialize + list_tools round trip: proves the middleware passes
    # legitimate traffic through without breaking the stream.
    assert "get_scene_info" in names


def test_bearer_token_admits_full_session_over_sse():
    pytest.importorskip("uvicorn")
    port = _free_port()
    server, thread = _serve(
        lambda: server_module._bearer_auth_middleware(mcp.sse_app(), "sekrit"), port
    )
    try:
        names = _run_client_flow(
            _list_tools_over_sse,
            f"http://{DEFAULT_HTTP_HOST}:{port}/sse",
            {"Authorization": "Bearer sekrit"},
        )
    finally:
        _stop(server, thread)
    # Same claim for the SSE transport, whose long-lived stream is what the
    # raw-ASGI middleware design exists to protect.
    assert "get_scene_info" in names
