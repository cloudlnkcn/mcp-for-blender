"""The HTTP side services: preview page, asset upload, result downloads.

The routes are plain Starlette and the file helpers are pure, so most of this
is unit-level. The bearer-middleware ?token= acceptance and the mounting next
to the MCP endpoints are covered here too, since that wiring is what makes the
services reachable (and keep the token's authority) in a real deployment.
"""

import asyncio
import json

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from blender_mcp import http_services, server
from blender_mcp.http_services import (
    resolve_file,
    safe_name,
    unique_path,
)


@pytest.fixture(autouse=True)
def _files_env(monkeypatch, tmp_path):
    """Point the managed directory at a throwaway and forget any listener."""
    monkeypatch.delenv("BLENDER_MCP_PUBLIC_URL", raising=False)
    monkeypatch.delenv("BLENDER_MCP_HTTP_TOKEN", raising=False)
    monkeypatch.delenv("BLENDER_MCP_MAX_UPLOAD_MB", raising=False)
    monkeypatch.delenv("BLENDER_MCP_HTTP_SERVICES", raising=False)
    monkeypatch.setenv("BLENDER_MCP_FILES_DIR", str(tmp_path / "files"))
    monkeypatch.setattr(http_services, "_listener", {})
    return tmp_path / "files"


@pytest.fixture
def client():
    return TestClient(Starlette(routes=http_services.routes()))


def test_safe_name_strips_everything_but_a_filename():
    assert safe_name("../../etc/passwd") == "passwd"
    assert safe_name("a/b\\c.glb") == "b_c.glb"
    assert safe_name("..hidden") == "hidden"
    assert safe_name("") == ""


def test_unique_path_does_not_clobber(tmp_path):
    first = unique_path(tmp_path, "m.glb")
    first.write_bytes(b"x")
    second = unique_path(tmp_path, "m.glb")
    assert first != second and second.name.startswith("m-")


def test_resolve_file_stays_inside_its_category(_files_env):
    uploaded = http_services.category_dir("uploads", create=True) / "a.glb"
    uploaded.write_bytes(b"x")
    assert resolve_file("uploads", "a.glb") == uploaded
    assert resolve_file("uploads", "..") is None
    assert resolve_file("nope", "a.glb") is None
    assert resolve_file("uploads", "missing.glb") is None


def test_upload_download_roundtrip(client):
    res = client.post("/upload/mesh.glb", content=b"GLB-bytes")
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "mesh.glb" and body["size"] == 9
    assert body["path"].endswith("mesh.glb")

    res = client.get("/files/uploads/mesh.glb")
    assert res.status_code == 200
    assert res.content == b"GLB-bytes"
    assert "attachment" in res.headers["content-disposition"]


def test_upload_names_are_sanitized_and_collisions_kept(client):
    res = client.post("/upload/re%20port.glb", content=b"1")
    assert res.status_code == 200 and res.json()["name"] == "re_port.glb"
    res = client.post("/upload/re_port.glb", content=b"2")
    assert res.status_code == 200 and res.json()["name"] != "re_port.glb"


def test_upload_rejects_empty_and_oversize(client, monkeypatch):
    assert client.post("/upload/x.glb", content=b"").status_code == 400
    monkeypatch.setenv("BLENDER_MCP_MAX_UPLOAD_MB", "1")
    assert client.post("/upload/big.bin", content=b"0" * (2 * 1024 * 1024)).status_code == 413


def test_download_rejects_unknown(client):
    assert client.get("/files/nope/a.glb").status_code == 404
    assert client.get("/files/uploads/missing.glb").status_code == 404


def test_files_listing_covers_the_categories(client):
    http_services.managed_path("exports", "s.glb").write_bytes(b"e")
    http_services.managed_path("renders", "r.png").write_bytes(b"r")
    client.post("/upload/u.glb", content=b"u")
    names = {(f["category"], f["name"]) for f in client.get("/files").json()["files"]}
    assert ("exports", "s.glb") in names and ("renders", "r.png") in names and ("uploads", "u.glb") in names
    only = client.get("/files?category=renders").json()["files"]
    assert {f["category"] for f in only} == {"renders"}


def test_preview_page_and_latest_image(client, monkeypatch):
    res = client.get("/preview")
    assert res.status_code == 200 and "text/html" in res.headers["content-type"]
    # A fresh store: other tests may have left a capture in the shared one.
    from blender_mcp.openai_apps import ViewportStore

    monkeypatch.setattr(server, "viewport_store", ViewportStore())
    assert client.get("/preview/latest.png").status_code == 404
    server.viewport_store.put(b"png-bytes", "user")
    res = client.get("/preview/latest.png")
    assert res.status_code == 200 and res.content == b"png-bytes"


def test_capture_endpoint_recaptures(client, monkeypatch):
    calls = []
    monkeypatch.setattr(server, "_store_capture", lambda size, source: calls.append((size, source)))
    assert client.post("/preview/capture").status_code == 200
    assert calls == [(1024, "user")]


def test_capture_failure_is_reported(client, monkeypatch):
    def boom(size, source):
        raise RuntimeError("blender is closed")

    monkeypatch.setattr(server, "_store_capture", boom)
    res = client.post("/preview/capture")
    assert res.status_code == 502 and "blender is closed" in res.json()["error"]


class _FakeBlender:
    def __init__(self, printed):
        self.printed = printed
        self.commands = []

    def send_command(self, command_type, params=None, read_only=False):
        self.commands.append((command_type, params, read_only))
        return {"result": self.printed}


def test_import_endpoint_runs_the_import_script(client, monkeypatch):
    fake = _FakeBlender("__MCP_RESULT__" + json.dumps(
        {"file": "/x/mesh.glb", "ext": ".glb", "imported": ["Mesh"], "images": []}))
    monkeypatch.setattr(server, "get_blender_connection", lambda: fake)
    client.post("/upload/mesh.glb", content=b"GLB")
    res = client.post("/files/uploads/mesh.glb/import")
    assert res.status_code == 200
    assert res.json()["imported"] == ["Mesh"]
    (command, params, read_only) = fake.commands[0]
    assert command == "execute_code" and read_only is False
    assert "/x/mesh.glb" in params["code"] or "mesh.glb" in params["code"]


def test_import_endpoint_reports_failure(client, monkeypatch):
    def no_blender():
        raise RuntimeError("not connected")

    client.post("/upload/mesh.glb", content=b"GLB")
    monkeypatch.setattr(server, "get_blender_connection", no_blender)
    res = client.post("/files/uploads/mesh.glb/import")
    assert res.status_code == 502 and "not connected" in res.json()["error"]


def test_bearer_token_via_header_or_query(monkeypatch):
    async def hello(request):
        return PlainTextResponse("ok")

    app = _bearer(Starlette(routes=[Route("/", hello, methods=["GET"])]), "s3cret")
    client = TestClient(app)
    assert client.get("/").status_code == 401
    assert client.get("/", headers={"Authorization": "Bearer s3cret"}).status_code == 200
    assert client.get("/", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/?token=s3cret").status_code == 200
    assert client.get("/?token=wrong").status_code == 401


def test_bearer_token_survives_url_percent_encoding():
    async def hello(request):
        return PlainTextResponse("ok")

    # '=' must be percent-encoded in a query value and still match.
    app = _bearer(Starlette(routes=[Route("/", hello, methods=["GET"])]), "s3=cret")
    client = TestClient(app)
    assert client.get("/?token=s3%3Dcret").status_code == 200
    assert client.get("/?token=s3%3Dwrong").status_code == 401


def _bearer(app, token):
    from blender_mcp.server import _bearer_auth_middleware

    return _bearer_auth_middleware(app, token)


def test_urls_need_a_listener(_files_env):
    assert http_services.urls() == {}
    http_services.set_listener("0.0.0.0", 8000)
    urls = http_services.urls()
    assert "/preview" in urls["preview"] and "/files" in urls["downloads"]
    assert "token" not in urls["preview"]
    exported = http_services.category_dir("exports", create=True) / "s.glb"
    exported.write_bytes(b"x")
    assert http_services.download_url(exported).endswith("/files/exports/s.glb")


def test_urls_honour_public_url_and_token(_files_env, monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_PUBLIC_URL", "https://blender.example.com:9443/")
    monkeypatch.setenv("BLENDER_MCP_HTTP_TOKEN", "s3cret")
    http_services.set_listener("0.0.0.0", 8000)
    urls = http_services.urls()
    assert urls["preview"] == "https://blender.example.com:9443/preview?token=s3cret"
    exported = http_services.category_dir("exports", create=True) / "s.glb"
    assert http_services.download_url(exported) == \
        "https://blender.example.com:9443/files/exports/s.glb?token=s3cret"


def test_download_url_ignores_paths_outside_the_root(_files_env):
    http_services.set_listener("127.0.0.1", 8000)
    assert http_services.download_url("/etc/passwd") is None
    assert http_services.download_url(_files_env / "stray.glb") is None


def test_services_can_be_switched_off(_files_env, monkeypatch):
    monkeypatch.setenv("BLENDER_MCP_HTTP_SERVICES", "0")
    http_services.set_listener("127.0.0.1", 8000)
    assert not http_services.active()
    assert http_services.urls() == {}


def test_routes_mount_next_to_the_mcp_endpoints():
    app = server.mcp.streamable_http_app()
    app.router.routes.extend(http_services.routes())
    paths = {getattr(r, "path", None) for r in app.router.routes}
    assert {"/mcp", "/preview", "/preview/capture", "/upload/{name}", "/files"} <= paths


def test_disabled_services_are_not_mounted(monkeypatch, _files_env):
    monkeypatch.setenv("BLENDER_MCP_HTTP_SERVICES", "0")
    calls = _patch_uvicorn(monkeypatch)
    server._run_http_transport("streamable-http", "127.0.0.1", 8765, False)
    paths = {getattr(r, "path", None) for r in calls["app"].router.routes}
    assert "/mcp" in paths and "/preview" not in paths
    assert not http_services.active()


def test_http_transport_mounts_services(monkeypatch, _files_env):
    calls = _patch_uvicorn(monkeypatch)
    server._run_http_transport("streamable-http", "127.0.0.1", 8765, False)
    paths = {getattr(r, "path", None) for r in calls["app"].router.routes}
    assert {"/mcp", "/preview", "/upload/{name}", "/files"} <= paths
    assert http_services.active()


def _patch_uvicorn(monkeypatch):
    # _run_http_transport mutates module-global FastMCP settings; pin them so
    # this test leaves nothing behind.
    monkeypatch.setattr(mcp_settings := server.mcp.settings, "host", mcp_settings.host)
    monkeypatch.setattr(mcp_settings, "port", mcp_settings.port)
    monkeypatch.setattr(mcp_settings, "stateless_http", mcp_settings.stateless_http)
    monkeypatch.setattr(mcp_settings, "transport_security", mcp_settings.transport_security)

    calls = {}

    def fake_run(app, host, port, log_level):
        calls.update(app=app, host=host, port=port)

    monkeypatch.setattr("uvicorn.run", fake_run)
    return calls
