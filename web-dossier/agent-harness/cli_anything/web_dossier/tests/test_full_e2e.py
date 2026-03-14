"""E2E and subprocess tests for cli-anything-web-dossier."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def _resolve_cli(name: str) -> list[str]:
    """Resolve installed CLI command; fallback to python -m in dev."""
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
    module = "cli_anything.web_dossier.web_dossier_cli"
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m {module}")
    return [sys.executable, "-m", module]


class TestCLISubprocess:
    CLI_BASE = _resolve_cli("cli-anything-web-dossier")

    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise AssertionError(
                f"Command failed ({result.returncode}): {' '.join(args)}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        return result

    @staticmethod
    def _make_min_repo(base: Path) -> Path:
        (base / "production").mkdir(parents=True, exist_ok=True)
        (base / "tests" / "integration").mkdir(parents=True, exist_ok=True)
        (base / "README.md").write_text("web-dossier", encoding="utf-8")
        (base / "tests" / "integration" / "package.json").write_text("{}", encoding="utf-8")
        return base

    def test_help(self):
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "web-dossier CLI" in result.stdout

    def test_doctor_json(self):
        result = self._run(["--json", "doctor"])
        data = json.loads(result.stdout)
        assert "tools" in data
        assert "git" in data["tools"]

    def test_project_init_and_info(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            repo = self._make_min_repo(tmp / "repo")
            proj = tmp / "proj.json"

            init = self._run([
                "--json",
                "project",
                "init",
                "--source",
                str(repo),
                "-o",
                str(proj),
            ])
            data = json.loads(init.stdout)
            assert Path(data["saved"]).exists()

            info = self._run(["--json", "--project", str(proj), "project", "info"])
            payload = json.loads(info.stdout)
            assert payload["name"] == "web-dossier"

    def test_pipeline_list_from_project(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            repo = self._make_min_repo(tmp / "repo")
            proj = tmp / "proj.json"
            self._run(["project", "init", "--source", str(repo), "-o", str(proj)])

            listed = self._run(["--json", "--project", str(proj), "pipeline", "list"])
            data = json.loads(listed.stdout)
            assert "build-war" in data["pipelines"]

    def test_run_command_dry_run(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            repo = self._make_min_repo(tmp / "repo")
            result = self._run([
                "--json",
                "--source",
                str(repo),
                "run",
                "command",
                "--dry-run",
                "--",
                "python3",
                "-c",
                "print('hello')",
            ])
            data = json.loads(result.stdout)
            assert data["dry_run"] is True
            assert data["success"] is True

    def test_run_command_real_execution(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            repo = self._make_min_repo(tmp / "repo")
            artifact = tmp / "artifact.txt"
            code = f"from pathlib import Path; Path(r'{artifact}').write_text('ok', encoding='utf-8'); print('done')"
            result = self._run([
                "--json",
                "--source",
                str(repo),
                "run",
                "command",
                "--",
                "python3",
                "-c",
                code,
            ])
            data = json.loads(result.stdout)
            assert data["success"] is True
            assert artifact.exists()
            assert artifact.read_text(encoding="utf-8") == "ok"
            print(f"\n  Artifact: {artifact} ({artifact.stat().st_size} bytes)")
