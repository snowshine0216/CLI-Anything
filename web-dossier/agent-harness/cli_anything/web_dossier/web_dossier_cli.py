#!/usr/bin/env python3
"""CLI harness for web-dossier repository workflows."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
from typing import Any, Optional, Dict

import click

from cli_anything.web_dossier.core import project as project_mod
from cli_anything.web_dossier.core import pipeline as pipeline_mod
from cli_anything.web_dossier.core.session import Session
from cli_anything.web_dossier.utils import web_dossier_backend as backend
from cli_anything.web_dossier.utils.repl_skin import ReplSkin


_json_output = False
_repl_mode = False
_session = Session()


def _emit(data: Any, message: str = "") -> None:
    if _json_output:
        click.echo(json.dumps(data, indent=2, default=str))
        return
    if message:
        click.echo(message)
    if isinstance(data, dict):
        for key, value in data.items():
            click.echo(f"{key}: {value}")
    elif isinstance(data, list):
        for item in data:
            click.echo(f"- {item}")
    else:
        click.echo(str(data))


def _fail(message: str, code: int = 1) -> None:
    if _json_output:
        click.echo(json.dumps({"error": message, "code": code}))
    else:
        click.echo(f"Error: {message}", err=True)
    if not _repl_mode:
        raise click.exceptions.Exit(code)


def _session_default_path() -> str:
    primary = Path.home() / ".cli-anything-web-dossier"
    try:
        primary.mkdir(parents=True, exist_ok=True)
        return str(primary / "session.json")
    except (PermissionError, OSError):
        fallback = Path(tempfile.gettempdir()) / ".cli-anything-web-dossier"
        fallback.mkdir(parents=True, exist_ok=True)
        return str(fallback / "session.json")


def _effective_source(source: Optional[str] = None, project: Optional[Dict[str, Any]] = None) -> str:
    if source:
        return str(Path(source).resolve())
    if project and project.get("source_path"):
        return str(Path(project["source_path"]).resolve())
    if _session.state.source_path:
        return _session.state.source_path
    _fail("No source path set. Use --source or `config source-set`.")
    return ""


def _effective_project(project_path: Optional[str]) -> Optional[Dict[str, Any]]:
    chosen = project_path or _session.state.project_path
    if not chosen:
        return None
    return project_mod.load_project(chosen)


def _require_project(project_path: Optional[str]) -> Dict[str, Any]:
    project = _effective_project(project_path)
    if project is None:
        _fail("Project file required. Use --project or `project init` first.")
    return project


@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Output machine-readable JSON")
@click.option("--session-file", default=None, help="Session file path")
@click.option("--source", default=None, help="Source repository path")
@click.option("--project", "project_path", default=None, help="Project file path")
@click.pass_context
def cli(ctx: click.Context, use_json: bool, session_file: Optional[str], source: Optional[str], project_path: Optional[str]):
    """web-dossier CLI for build/test and CI workflows.

    Run with no subcommand to enter REPL mode.
    """
    global _json_output
    _json_output = use_json

    sf = session_file or _session_default_path()
    _session.load(sf)
    ctx.obj = {"session_file": sf}

    if source:
        _session.set_source_path(str(Path(source).resolve()))
    if project_path:
        _session.set_project_path(str(Path(project_path).resolve()))

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


@cli.group()
def project():
    """Project file operations."""


@project.command("init")
@click.option("--source", "source_path", required=True, help="web-dossier repository path")
@click.option("--name", default="web-dossier")
@click.option("-o", "output", required=True, help="Project output path")
def project_init(source_path: str, name: str, output: str):
    validation = project_mod.validate_source_path(source_path)
    if not validation["valid"]:
        _fail(f"Invalid source path. Missing markers: {validation['missing_markers']}")
    project_data = project_mod.create_project(source_path=source_path, name=name)
    saved = project_mod.save_project(project_data, output)
    _session.set_source_path(project_data["source_path"])
    _session.set_project_path(str(Path(saved).resolve()))
    _emit({"saved": saved, "project": project_mod.project_info(project_data)}, "Project initialized")


@project.command("info")
@click.option("--project", "project_path", default=None)
def project_info_cmd(project_path: Optional[str]):
    project_data = _require_project(project_path)
    _emit(project_mod.project_info(project_data))


@project.command("validate")
@click.option("--source", "source_path", default=None)
def project_validate(source_path: Optional[str]):
    eff_source = _effective_source(source_path)
    _emit(project_mod.validate_source_path(eff_source))


@cli.group()
def config():
    """Session config and custom pipelines."""


@config.command("show")
def config_show():
    _emit(_session.to_dict())


@config.command("source-set")
@click.argument("source_path")
def config_source_set(source_path: str):
    resolved = str(Path(source_path).resolve())
    _session.set_source_path(resolved)
    _emit({"source_path": resolved}, "Source path updated")


@config.command("pipeline-add")
@click.option("--name", required=True)
@click.option("--cwd", default=".")
@click.option("--command", "command_str", required=True, help="Quoted command string")
def config_pipeline_add(name: str, cwd: str, command_str: str):
    steps = pipeline_mod.parse_custom_command(command_str, cwd=cwd, name=name)
    _session.set_pipeline(name, steps)
    _emit({"name": name, "steps": steps}, "Custom pipeline added")


@config.command("pipeline-remove")
@click.argument("name")
def config_pipeline_remove(name: str):
    removed = _session.remove_pipeline(name)
    if not removed:
        _fail(f"Pipeline not found: {name}")
    _emit({"removed": name}, "Custom pipeline removed")


@cli.group()
def session():
    """Session state operations."""


@session.command("status")
def session_status():
    _emit(_session.to_dict())


@session.command("save")
@click.pass_context
def session_save(ctx: click.Context):
    path = _session.save(ctx.obj["session_file"])
    _emit({"saved": path}, "Session saved")


@session.command("load")
@click.pass_context
def session_load(ctx: click.Context):
    ok = _session.load(ctx.obj["session_file"])
    if not ok:
        _fail("Session file does not exist")
    _emit({"loaded": ctx.obj["session_file"]}, "Session loaded")


@session.command("undo")
def session_undo():
    if not _session.undo():
        _fail("Nothing to undo")
    _emit(_session.to_dict(), "Undo applied")


@session.command("redo")
def session_redo():
    if not _session.redo():
        _fail("Nothing to redo")
    _emit(_session.to_dict(), "Redo applied")


@cli.group()
def pipeline():
    """Pipeline operations."""


@pipeline.command("list")
@click.option("--project", "project_path", default=None)
def pipeline_list(project_path: Optional[str]):
    project_data = _effective_project(project_path)
    project_pipelines = project_data.get("pipelines", {}) if project_data else {}
    merged = pipeline_mod.merge_pipelines(_session.state.custom_pipelines)
    merged.update(project_pipelines)
    _emit(
        {
            "pipeline_count": len(merged),
            "pipelines": sorted(merged.keys()),
        }
    )


@pipeline.command("run")
@click.argument("name")
@click.option("--project", "project_path", default=None)
@click.option("--source", "source_path", default=None)
@click.option("--timeout", default=3600, show_default=True, type=int)
@click.option("--dry-run", is_flag=True)
def pipeline_run(name: str, project_path: Optional[str], source_path: Optional[str], timeout: int, dry_run: bool):
    project_data = _effective_project(project_path)
    merged = pipeline_mod.merge_pipelines(_session.state.custom_pipelines)
    if project_data:
        merged.update(project_data.get("pipelines", {}))

    if name not in merged:
        _fail(f"Pipeline not found: {name}")

    source = _effective_source(source_path, project_data)
    result = backend.run_pipeline(source_path=source, steps=merged[name], timeout=timeout, dry_run=dry_run)
    if not result["success"]:
        _emit(result)
        _fail(f"Pipeline failed: {name}")
    _emit(result, f"Pipeline succeeded: {name}")


@cli.group()
def run():
    """Execute one-off commands from source repo."""


@run.command("command")
@click.option("--source", "source_path", default=None)
@click.option("--cwd", default=".")
@click.option("--timeout", default=3600, show_default=True, type=int)
@click.option("--dry-run", is_flag=True)
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
def run_command(source_path: Optional[str], cwd: str, timeout: int, dry_run: bool, command: tuple[str, ...]):
    if not command:
        _fail("Command is required after `run command`.")
    source = _effective_source(source_path)
    result = backend.run_command(source_path=source, command=list(command), cwd=cwd, timeout=timeout, dry_run=dry_run)
    if not result["success"]:
        _emit(result)
        _fail("Command failed")
    _emit(result)


@cli.command("doctor")
def doctor():
    _emit(backend.doctor())


@cli.command("repl")
@click.option("--project", "project_path", default=None)
def repl(project_path: Optional[str]):
    """Interactive REPL mode."""
    global _repl_mode
    _repl_mode = True
    skin = ReplSkin("web-dossier", version="1.0.0")
    skin.print_banner()

    if project_path:
        _session.set_project_path(str(Path(project_path).resolve()))

    while True:
        project_name = Path(_session.state.project_path).name if _session.state.project_path else ""
        line = ""
        try:
            line = input(skin.prompt(project_name=project_name, modified=_session.state.modified))
        except (EOFError, KeyboardInterrupt):
            click.echo()
            break

        line = line.strip()
        if not line:
            continue
        if line in {"quit", "exit", ":q"}:
            break
        if line == "help":
            click.echo("Try: project info | project validate | pipeline list | pipeline run build-war | doctor | session save")
            continue

        try:
            args = shlex.split(line)
            cli.main(args=args, prog_name="cli-anything-web-dossier", standalone_mode=False)
        except SystemExit:
            continue
        except Exception as exc:
            _fail(str(exc))

    skin.print_goodbye()
    _repl_mode = False


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
