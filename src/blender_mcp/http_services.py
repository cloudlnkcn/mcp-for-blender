"""HTTP side services for docker/remote deployments, served next to MCP.

When the server runs with --transport http or sse, the ASGI app also mounts a
handful of plain HTTP routes so a human (or another machine) can work with the
design without an MCP client in the loop:

- GET  /preview                     live viewport page (auto-refreshing screenshot, upload form, downloads)
- GET  /preview/latest.png          the newest viewport capture as PNG
- POST /preview/capture             capture a fresh screenshot from Blender now
- POST /upload/{filename}           store an asset next to Blender; body is the raw file bytes
- GET  /files                       list uploads, exports and renders as JSON
- GET  /files/{category}/{name}     download one file
- POST /files/uploads/{name}/import import an uploaded file into the Blender scene

Everything shares the MCP app's bearer token when one is set (header, or
?token= for browser links). Files live under one managed directory -- by
default ~/.blender-mcp/files, override with BLENDER_MCP_FILES_DIR -- because
the addon and this server are expected to share a filesystem (screenshots are
exchanged through temp paths the same way). Set BLENDER_MCP_HTTP_SERVICES=0 to
turn the routes off while keeping MCP over HTTP.
"""

import mimetypes
import os
import re
import socket
import time
from pathlib import Path

from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.routing import Route

# uploads (assets arriving from outside), exports (export_scene output) and
# renders (render_scene output) are the three buckets the download routes serve.
CATEGORIES = ("uploads", "exports", "renders")

SERVICES_DISABLED_ENV = "BLENDER_MCP_HTTP_SERVICES"
FILES_DIR_ENV = "BLENDER_MCP_FILES_DIR"
PUBLIC_URL_ENV = "BLENDER_MCP_PUBLIC_URL"
MAX_UPLOAD_MB_ENV = "BLENDER_MCP_MAX_UPLOAD_MB"
DEFAULT_MAX_UPLOAD_MB = 512

_listener: dict = {}


def services_enabled() -> bool:
    return os.getenv(SERVICES_DISABLED_ENV, "1").strip().lower() not in {"0", "false", "no", "off"}


def set_listener(host: str, port: int) -> None:
    """Remember where the HTTP transport is listening, so tool results and the
    addon-status payload can advertise working URLs. Not set over stdio."""
    _listener["host"] = host
    _listener["port"] = port


def active() -> bool:
    return services_enabled() and bool(_listener)


def files_root() -> Path:
    root = os.getenv(FILES_DIR_ENV)
    if root:
        return Path(root).expanduser()
    return Path.home() / ".blender-mcp" / "files"


def category_dir(category: str, create: bool = False) -> Path:
    path = files_root() / category
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_name(name: str) -> str:
    """A filename that is just a filename: basenamed, no separators or dots
    leading it, short. Used for uploads and to reject download paths."""
    name = os.path.basename(name or "").strip()
    name = _SAFE_NAME.sub("_", name).lstrip(".")
    return name[:180]


def unique_path(directory: Path, name: str) -> Path:
    candidate = directory / name
    if not candidate.exists():
        return candidate
    stem, suffix = os.path.splitext(name)
    for i in range(1, 1000):
        candidate = directory / f"{stem}-{i}{suffix}"
        if not candidate.exists():
            return candidate
    return directory / f"{stem}-{int(time.time())}{suffix}"


def resolve_file(category: str, name: str) -> Path | None:
    """The file a download route may serve, or None. safe_name already removed
    every separator; resolving inside the category dir is belt and braces."""
    if category not in CATEGORIES:
        return None
    clean = safe_name(name)
    if not clean:
        return None
    base = category_dir(category)
    path = base / clean
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


def max_upload_bytes() -> int:
    raw = os.getenv(MAX_UPLOAD_MB_ENV, str(DEFAULT_MAX_UPLOAD_MB))
    try:
        return max(1, int(raw)) * 1024 * 1024
    except ValueError:
        return DEFAULT_MAX_UPLOAD_MB * 1024 * 1024


def _local_ip() -> str | None:
    """The address this machine would source traffic from. UDP connect sends
    no packets; it just makes the OS pick a local address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


def public_base_url() -> str:
    """Where a browser outside this machine should reach the services.

    BLENDER_MCP_PUBLIC_URL wins outright (docker port mappings are not visible
    from inside the container). A wildcard bind advertises the container's own
    address as a best effort.
    """
    override = os.getenv(PUBLIC_URL_ENV, "").strip().rstrip("/")
    if override:
        return override
    host = str(_listener.get("host", "127.0.0.1"))
    port = int(_listener.get("port", 8000))
    shown = host.strip("[]")
    if shown in ("0.0.0.0", "::", "*"):
        shown = _local_ip() or "localhost"
    if ":" in shown and not shown.startswith("["):
        shown = f"[{shown}]"
    return f"http://{shown}:{port}"


def _token_hint() -> str:
    token = os.getenv("BLENDER_MCP_HTTP_TOKEN", "").strip()
    return f"?token={token}" if token else ""


def preview_url() -> str | None:
    return f"{public_base_url()}/preview{_token_hint()}" if active() else None


def urls() -> dict:
    """The service URLs get_addon_status advertises, or {} over stdio, where
    there is no HTTP listener to point at."""
    if not active():
        return {}
    base = public_base_url()
    out = {
        "preview": f"{base}/preview{_token_hint()}",
        "upload": f"POST {base}/upload/{{filename}} with the raw file bytes, then import_file() it",
        "downloads": f"{base}/files{_token_hint()}",
    }
    if not _token_hint():
        out["note"] = (
            "Set BLENDER_MCP_HTTP_TOKEN to require a token if this port is reachable "
            "from outside; with a token set, add ?token=... to these URLs in a browser."
        )
    return out


def managed_path(category: str, name: str) -> Path:
    return unique_path(category_dir(category, create=True), safe_name(name))


def download_url(path: str | Path) -> str | None:
    """The /files URL for a path inside the managed directory, else None."""
    if not active():
        return None
    try:
        rel = Path(path).resolve().relative_to(files_root().resolve())
    except (ValueError, OSError):
        return None
    parts = rel.parts
    if len(parts) != 2 or parts[0] not in CATEGORIES:
        return None
    return f"{public_base_url()}/files/{parts[0]}/{parts[1]}{_token_hint()}"


def _json_error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status_code)


async def preview_page(request: Request) -> Response:
    return HTMLResponse(_PREVIEW_HTML)


async def preview_latest(request: Request) -> Response:
    from . import server

    _, png = server._viewport_snapshot()
    if png is None:
        return _json_error("No capture yet - POST /preview/capture first", status_code=404)
    return Response(png, media_type="image/png", headers={"Cache-Control": "no-store"})


async def preview_capture(request: Request) -> Response:
    import anyio

    from . import server

    try:
        await anyio.to_thread.run_sync(lambda: server._store_capture(1024, "user"))
    except Exception as e:
        return _json_error(f"Capture failed: {e}", status_code=502)
    return JSONResponse({"url": "/preview/latest.png", "captured_at": time.time()})


async def upload(request: Request) -> Response:
    name = safe_name(request.path_params.get("name", ""))
    if not name:
        return _json_error("A filename is required: POST /upload/{filename}")
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > max_upload_bytes():
        return _json_error("File larger than the upload limit", status_code=413)

    limit = max_upload_bytes()
    chunks, total = [], 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            return _json_error("File larger than the upload limit", status_code=413)
        chunks.append(chunk)
    if total == 0:
        return _json_error("Empty body: POST the raw file bytes, e.g. curl --data-binary @model.glb")

    path = managed_path("uploads", name)
    with open(path, "wb") as f:
        for chunk in chunks:
            f.write(chunk)

    return JSONResponse({
        "name": path.name,
        "path": str(path),
        "size": total,
        "url": f"/files/uploads/{path.name}{_token_hint()}",
        "import": f"POST /files/uploads/{path.name}/import to bring it into the scene",
    })


async def list_files(request: Request) -> Response:
    only = request.query_params.get("category")
    categories = [only] if only in CATEGORIES else list(CATEGORIES)
    files = []
    for category in categories:
        directory = category_dir(category)
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if not path.is_file() or path.name.startswith("."):
                continue
            stat = path.stat()
            files.append({
                "category": category,
                "name": path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "url": f"/files/{category}/{path.name}{_token_hint()}",
            })
    files.sort(key=lambda f: -f["modified"])
    return JSONResponse({"root": str(files_root()), "files": files})


async def download(request: Request) -> Response:
    path = resolve_file(request.path_params.get("category", ""), request.path_params.get("name", ""))
    if path is None:
        return _json_error("No such file", status_code=404)
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=path.name)


async def import_uploaded(request: Request) -> Response:
    import anyio

    from . import blender_scripts, server

    path = resolve_file("uploads", request.path_params.get("name", ""))
    if path is None:
        return _json_error("No such uploaded file", status_code=404)
    code = blender_scripts.build(blender_scripts.IMPORT, {"filepath": str(path)})

    def work():
        blender = server.get_blender_connection()
        return blender.send_command("execute_code", {"code": code})

    try:
        result = await anyio.to_thread.run_sync(work)
        imported = blender_scripts.parse_result(result.get("result", "") if isinstance(result, dict) else "")
    except Exception as e:
        return _json_error(f"Import failed: {e}", status_code=502)
    return JSONResponse({"file": path.name, **imported})


def routes() -> list[Route]:
    return [
        Route("/preview", preview_page, methods=["GET"]),
        Route("/preview/latest.png", preview_latest, methods=["GET"]),
        Route("/preview/capture", preview_capture, methods=["POST"]),
        Route("/upload/{name}", upload, methods=["POST"]),
        Route("/files", list_files, methods=["GET"]),
        Route("/files/{category}/{name}", download, methods=["GET"]),
        Route("/files/uploads/{name}/import", import_uploaded, methods=["POST"]),
    ]


_PREVIEW_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MCP for Blender - Preview</title>
<style>
  :root { color-scheme: dark; }
  body { font-family: system-ui, sans-serif; background: #1d1d1d; color: #ddd; margin: 0 auto; padding: 1rem 1.25rem 3rem; max-width: 60rem; }
  h1 { font-size: 1.1rem; } h2 { font-size: .95rem; margin-top: 1.75rem; color: #aaa; }
  #shot { display: block; width: 100%; border: 1px solid #333; border-radius: 6px; background: #111; min-height: 3rem; }
  button, input[type=submit] { background: #4670da; color: #fff; border: 0; border-radius: 4px; padding: .4rem .8rem; cursor: pointer; font-size: .85rem; }
  button:disabled { opacity: .5; cursor: default; }
  table { border-collapse: collapse; width: 100%; font-size: .85rem; }
  td, th { text-align: left; padding: .25rem .5rem; border-bottom: 1px solid #2c2c2c; }
  td a { color: #8ab4ff; } td form { display: inline; }
  .muted { color: #777; font-size: .8rem; }
  #status { margin-left: .6rem; font-size: .8rem; color: #999; }
  input[type=file] { font-size: .85rem; }
  #flash { color: #d9a; font-size: .85rem; min-height: 1.2rem; }
</style>
</head>
<body>
<h1>MCP for Blender &mdash; live preview <span id="status"></span></h1>
<div><img id="shot" alt="Blender viewport"></div>
<p><button id="capture">Capture now</button> <label><input type="checkbox" id="auto" checked> auto-refresh</label>
   <span id="stale"></span></p>

<h2>Send an asset to Blender</h2>
<p><input type="file" id="picker" multiple> <span class="muted">Files land in the uploads folder; import pulls them into the scene.</span></p>
<p id="flash"></p>

<h2>Files</h2>
<p><button id="refresh">Refresh</button> <span class="muted">uploads, exports and renders from the shared files directory</span></p>
<table id="files"><thead><tr><th>category</th><th>name</th><th>size</th><th></th></tr></thead><tbody></tbody></table>

<script>
const TOKEN = new URLSearchParams(location.search).get("token") || sessionStorage.getItem("bmcp_token") || "";
if (TOKEN) sessionStorage.setItem("bmcp_token", TOKEN);
const q = extra => new URLSearchParams({...(TOKEN ? {token: TOKEN} : {}), ...(extra || {})}).toString();
const shot = document.getElementById("shot"), status = document.getElementById("status"), stale = document.getElementById("stale");

function refreshShot() {
  const img = new Image();
  img.onload = () => { shot.src = img.src; status.textContent = "updated " + new Date().toLocaleTimeString(); stale.textContent = ""; };
  img.onerror = () => { status.textContent = "no capture yet"; };
  img.src = "/preview/latest.png?" + q({t: Date.now()});
}
setInterval(() => { if (document.getElementById("auto").checked) refreshShot(); }, 3000);
refreshShot();

async function post(url) {
  const res = await fetch(url, {method: "POST"});
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || res.status);
  return body;
}
document.getElementById("capture").onclick = async e => {
  e.target.disabled = true;
  try { await post("/preview/capture" + (TOKEN ? "?token=" + encodeURIComponent(TOKEN) : "")); refreshShot(); }
  catch (err) { stale.textContent = "capture failed: " + err.message; }
  e.target.disabled = false;
};

const flash = document.getElementById("flash");
function say(text) { flash.textContent = text; }
document.getElementById("picker").onchange = async e => {
  for (const file of e.target.files) {
    try {
      say("uploading " + file.name + "...");
      const res = await fetch("/upload/" + encodeURIComponent(file.name) + (TOKEN ? "?token=" + encodeURIComponent(TOKEN) : ""),
                              {method: "POST", body: file});
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.error || res.status);
      say(file.name + " uploaded. Importing...");
      const done = await post("/files/uploads/" + encodeURIComponent(body.name) + "/import" + (TOKEN ? "?token=" + encodeURIComponent(TOKEN) : ""));
      say(`imported: ${(done.imported || []).join(", ") || "nothing new"}`);
    } catch (err) { say(file.name + " failed: " + err.message); }
  }
  e.target.value = "";
  refresh();
};

async function refresh() {
  const tbody = document.querySelector("#files tbody");
  try {
    const res = await fetch("/files?" + q());
    const body = await res.json();
    tbody.innerHTML = "";
    for (const f of body.files || []) {
      const row = tbody.insertRow();
      row.insertCell().textContent = f.category;
      const nameCell = row.insertCell();
      const a = document.createElement("a");
      a.href = f.url; a.textContent = f.name;
      nameCell.appendChild(a);
      row.insertCell().textContent = (f.size / 1024).toFixed(1) + " KB";
      if (f.category === "uploads") {
        const cell = row.insertCell();
        const btn = document.createElement("button");
        btn.textContent = "import";
        btn.onclick = async () => {
          try { const done = await post("/files/uploads/" + encodeURIComponent(f.name) + "/import" + (TOKEN ? "?token=" + encodeURIComponent(TOKEN) : ""));
                say(`imported: ${(done.imported || []).join(", ") || "nothing new"}`); }
          catch (err) { say("import failed: " + err.message); }
        };
        cell.appendChild(btn);
      } else row.insertCell();
    }
  } catch (err) { say("listing failed: " + err.message); }
}
document.getElementById("refresh").onclick = refresh;
refresh();
</script>
</body>
</html>
"""
