"""export_scene, render_scene and import_file: the managed-folder file tools.

Tool bodies run through the trajectory decorators exactly as in production;
Blender is a fake connection (or the script runner is a stub), so what's under
test is the plumbing: where files land, what the results tell the model, and
how failures read.
"""

import asyncio
import json

import pytest

from blender_mcp import http_services, server


@pytest.fixture(autouse=True)
def _files_env(monkeypatch, tmp_path):
    monkeypatch.delenv("BLENDER_MCP_PUBLIC_URL", raising=False)
    monkeypatch.delenv("BLENDER_MCP_HTTP_TOKEN", raising=False)
    monkeypatch.delenv("BLENDER_MCP_HTTP_SERVICES", raising=False)
    monkeypatch.setenv("BLENDER_MCP_FILES_DIR", str(tmp_path / "files"))
    monkeypatch.setattr(http_services, "_listener", {})
    return tmp_path / "files"


class FakeBlender:
    def __init__(self, result):
        self.result = result
        self.commands = []

    def send_command(self, command_type, params=None, read_only=False):
        self.commands.append((command_type, params))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_export_scene_exports_into_the_managed_folder(monkeypatch, _files_env):
    http_services.set_listener("127.0.0.1", 8000)
    sent = {}

    class B:
        def send_command(self, command_type, params=None, read_only=False):
            assert command_type == "export_scene"
            sent.update(params)
            return {"path": params["filepath"], "bytes": 12, "selection_only": False,
                    "exported": ["Cube", "Lamp"]}

    monkeypatch.setattr(server, "get_blender_connection", B)
    text = asyncio.run(server.export_scene(None, object_names=["Cube"]))

    assert "Cube" in text and "12 bytes" in text
    assert "Download: " in text and "/files/exports/" in text
    assert sent["format"] == "glb"
    assert sent["filepath"].startswith(str(_files_env / "exports" / "scene_"))


def test_export_scene_without_services_has_no_download_link(monkeypatch):
    class B:
        def send_command(self, command_type, params=None, read_only=False):
            return {"path": params["filepath"], "bytes": 3, "exported": ["Cube"]}

    monkeypatch.setattr(server, "get_blender_connection", B)
    text = asyncio.run(server.export_scene(None))
    assert "Download:" not in text


def test_export_scene_rejects_unknown_format():
    text = asyncio.run(server.export_scene(None, format="obj"))
    assert text.startswith("Error: format must be glb or fbx")


def test_export_scene_points_at_an_addon_update(monkeypatch):
    fake = FakeBlender(Exception("Unknown command type: export_scene"))
    monkeypatch.setattr(server, "get_blender_connection", lambda: fake)
    text = asyncio.run(server.export_scene(None))
    assert "install-addon" in text


def test_render_scene_attaches_previews_and_links(monkeypatch, _files_env):
    http_services.set_listener("127.0.0.1", 8000)
    full = _files_env / "renders" / "r_front.png"
    preview = _files_env / "renders" / "r_front_preview.png"
    full.parent.mkdir(parents=True)
    full.write_bytes(b"PNG")
    preview.write_bytes(b"small-png")

    seen = {}

    def fake_run_script(script, args):
        seen["script"] = script
        seen["args"] = args
        return {"renders": [{"view": "front", "path": str(full), "bytes": 3,
                             "preview": str(preview), "width": 8, "height": 8}],
                "engine": "CYCLES"}

    monkeypatch.setattr(server, "_run_script", fake_run_script)
    result = asyncio.run(server.render_scene(None, views=["front"], samples=32))

    assert seen["args"]["outdir"] == str(_files_env / "renders")
    assert seen["args"]["samples"] == 32
    assert not result.isError
    summary = result.content[0].text
    assert "CYCLES" in summary and str(full) in summary and "Download: " in summary
    image = result.content[1]
    assert image.type == "image" and image.mimeType == "image/png"


def test_render_scene_rejects_bad_views():
    result = asyncio.run(server.render_scene(None, views=["diagonal"]))
    assert result.isError and "Unknown view" in result.content[0].text


def test_render_scene_reports_failure(monkeypatch):
    def boom(script, args):
        raise RuntimeError("Cycles ran out of memory")

    monkeypatch.setattr(server, "_run_script", boom)
    result = asyncio.run(server.render_scene(None))
    assert result.isError and "Cycles ran out of memory" in result.content[0].text


def test_render_scene_all_failed_views_is_an_error(monkeypatch):
    monkeypatch.setattr(server, "_run_script", lambda s, a: {"renders": [
        {"view": "front", "error": "nope"}]})
    result = asyncio.run(server.render_scene(None))
    assert result.isError and "nope" in result.content[0].text


def test_import_file_reports_the_new_objects(monkeypatch):
    printed = "__MCP_RESULT__" + json.dumps(
        {"file": "/files/uploads/mesh.glb", "ext": ".glb", "imported": ["Mesh"], "images": []})
    fake = FakeBlender({"result": printed})
    monkeypatch.setattr(server, "get_blender_connection", lambda: fake)
    text = asyncio.run(server.import_file(None, filepath="/files/uploads/mesh.glb"))

    assert "Mesh" in text and "mesh.glb" in text
    (command, params) = fake.commands[0]
    assert command == "execute_code" and "mesh.glb" in params["code"]


def test_import_file_requires_a_path():
    assert asyncio.run(server.import_file(None, filepath="  ")).startswith("Error: filepath")


def test_import_file_surfaces_script_errors(monkeypatch):
    printed = "__MCP_RESULT__" + json.dumps(
        {"error": "No file at /nope.glb"})
    monkeypatch.setattr(server, "get_blender_connection",
                        lambda: FakeBlender({"result": printed}))
    text = asyncio.run(server.import_file(None, filepath="/nope.glb"))
    assert text == "Error: No file at /nope.glb"


def test_import_file_reports_old_addons(monkeypatch):
    monkeypatch.setattr(server, "get_blender_connection",
                        lambda: FakeBlender({"result": "printed without a marker"}))
    text = asyncio.run(server.import_file(None, filepath="/x.glb"))
    assert text.startswith("Error importing:")
