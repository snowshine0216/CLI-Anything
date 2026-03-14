"""Unit tests for cli_anything.web_dossier core modules."""

from __future__ import annotations

from pathlib import Path
import tempfile

from cli_anything.web_dossier.core import pipeline as pipeline_mod
from cli_anything.web_dossier.core import project as project_mod
from cli_anything.web_dossier.core.session import Session
from cli_anything.web_dossier.utils import web_dossier_backend as backend


def _make_min_repo(base: Path) -> Path:
    (base / "production").mkdir(parents=True, exist_ok=True)
    (base / "tests" / "integration").mkdir(parents=True, exist_ok=True)
    (base / "README.md").write_text("web-dossier", encoding="utf-8")
    (base / "tests" / "integration" / "package.json").write_text("{}", encoding="utf-8")
    return base


def test_validate_source_path_success(tmp_path: Path):
    repo = _make_min_repo(tmp_path / "repo")
    result = project_mod.validate_source_path(str(repo))
    assert result["valid"] is True
    assert result["missing_markers"] == []


def test_validate_source_path_missing_markers(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    result = project_mod.validate_source_path(str(repo))
    assert result["valid"] is False
    assert "README.md" in result["missing_markers"]


def test_project_roundtrip(tmp_path: Path):
    repo = _make_min_repo(tmp_path / "repo")
    proj = project_mod.create_project(str(repo), name="demo")
    out = tmp_path / "project.json"
    project_mod.save_project(proj, str(out))
    loaded = project_mod.load_project(str(out))
    assert loaded["name"] == "demo"
    assert "build-war" in loaded["pipelines"]


def test_project_info(tmp_path: Path):
    repo = _make_min_repo(tmp_path / "repo")
    proj = project_mod.create_project(str(repo), name="info")
    info = project_mod.project_info(proj)
    assert info["name"] == "info"
    assert info["pipeline_count"] > 0


def test_session_set_and_undo_redo():
    session = Session()
    session.set_source_path("/tmp/a")
    session.set_project_path("/tmp/p.json")
    assert session.state.project_path == "/tmp/p.json"

    assert session.undo() is True
    assert session.state.project_path == ""

    assert session.redo() is True
    assert session.state.project_path == "/tmp/p.json"


def test_session_save_load(tmp_path: Path):
    session = Session()
    session.set_source_path("/tmp/a")
    session.set_pipeline("x", [{"name": "x", "cwd": ".", "command": ["echo", "ok"]}])

    path = tmp_path / "session.json"
    session.save(str(path))

    loaded = Session()
    assert loaded.load(str(path)) is True
    assert loaded.state.source_path == "/tmp/a"
    assert "x" in loaded.state.custom_pipelines


def test_default_pipelines_have_expected_keys():
    d = pipeline_mod.default_pipelines()
    assert "build-war" in d
    assert "test-integration" in d


def test_parse_custom_command():
    steps = pipeline_mod.parse_custom_command("python -c 'print(42)'", cwd="scripts", name="smoke")
    assert steps[0]["name"] == "smoke"
    assert steps[0]["cwd"] == "scripts"
    assert steps[0]["command"][0] == "python"


def test_backend_run_command_dry_run(tmp_path: Path):
    repo = _make_min_repo(tmp_path / "repo")
    result = backend.run_command(str(repo), ["python3", "-c", "print('x')"], dry_run=True)
    assert result["success"] is True
    assert result["dry_run"] is True


def test_backend_run_pipeline_real_command(tmp_path: Path):
    repo = _make_min_repo(tmp_path / "repo")
    steps = [{"name": "echo", "cwd": ".", "command": ["python3", "-c", "print('hello')"]}]
    result = backend.run_pipeline(str(repo), steps)
    assert result["success"] is True
    assert "hello" in result["results"][0]["stdout"]


def test_backend_doctor_shape():
    result = backend.doctor()
    assert "tools" in result
    assert "git" in result["tools"]
