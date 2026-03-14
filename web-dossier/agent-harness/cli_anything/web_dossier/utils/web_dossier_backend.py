"""Backend wrapper around repository commands and executables."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any, Optional


def _resolve_executable(command: list[str], cwd: str) -> Optional[str]:
    if not command:
        return None
    exe = command[0]
    if exe.startswith("./"):
        abs_path = str(Path(cwd, exe).resolve())
        return abs_path if os.path.exists(abs_path) else None
    return shutil.which(exe)


def run_step(source_path: str, step: dict[str, Any], timeout: int = 3600, dry_run: bool = False) -> dict[str, Any]:
    rel_cwd = step.get("cwd", ".")
    cwd = str(Path(source_path, rel_cwd).resolve())
    command = step.get("command", [])
    name = step.get("name", "step")

    # In dry-run mode we only validate command shape and report execution metadata.
    # We intentionally do not require the executable to exist.
    if dry_run:
        if not command:
            raise RuntimeError(f"Step '{name}' has empty command.")
        return {
            "name": name,
            "cwd": cwd,
            "command": command,
            "dry_run": True,
            "success": True,
            "returncode": 0,
            "elapsed_sec": 0.0,
            "stdout": "",
            "stderr": "",
            "executable_check": "skipped",
        }

    resolved = _resolve_executable(command, cwd)
    if resolved is None:
        raise RuntimeError(
            f"Executable not found for step '{name}': {command[0] if command else '<empty>'}. "
            "Install required tools and ensure they are on PATH."
        )

    start = time.time()
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    elapsed = time.time() - start
    return {
        "name": name,
        "cwd": cwd,
        "command": command,
        "dry_run": False,
        "success": completed.returncode == 0,
        "returncode": completed.returncode,
        "elapsed_sec": round(elapsed, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_pipeline(source_path: str, steps: list[dict[str, Any]], timeout: int = 3600, dry_run: bool = False) -> dict[str, Any]:
    results = []
    for step in steps:
        result = run_step(source_path=source_path, step=step, timeout=timeout, dry_run=dry_run)
        results.append(result)
        if not result["success"]:
            break

    return {
        "source_path": str(Path(source_path).resolve()),
        "step_count": len(steps),
        "results": results,
        "success": all(x["success"] for x in results),
    }


def run_command(source_path: str, command: list[str], cwd: str = ".", timeout: int = 3600, dry_run: bool = False) -> dict[str, Any]:
    step = {
        "name": "run-command",
        "cwd": cwd,
        "command": command,
    }
    return run_step(source_path=source_path, step=step, timeout=timeout, dry_run=dry_run)


def doctor() -> dict[str, Any]:
    tool_names = ["git", "ant", "node", "npm", "npx"]
    tools = {name: shutil.which(name) for name in tool_names}
    return {
        "tools": tools,
        "ready_for_build": tools["ant"] is not None,
        "ready_for_integration_tests": all(tools[x] for x in ["node", "npm", "npx"]),
    }
