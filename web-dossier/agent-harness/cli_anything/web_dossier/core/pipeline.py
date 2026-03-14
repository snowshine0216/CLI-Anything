"""Pipeline definitions and resolution."""

from __future__ import annotations

import shlex
from typing import Any, Optional, Dict, List


def default_pipelines() -> dict[str, list[dict[str, Any]]]:
    return {
        "build-war": [
            {
                "name": "build-war",
                "cwd": ".",
                "command": ["ant", "-f", "production/build/build.xml", "build-war"],
            }
        ],
        "build-war-engineering": [
            {
                "name": "build-war-engineering",
                "cwd": "production/build",
                "command": ["./build-war.sh"],
            }
        ],
        "test-integration": [
            {
                "name": "integration-test",
                "cwd": "tests/integration",
                "command": ["npm", "test"],
            }
        ],
        "lint-pr-handler": [
            {
                "name": "pr-handler-lint",
                "cwd": "pull-request/pullRequestHandler",
                "command": ["npm", "run", "lint"],
            }
        ],
        "wdio-regression": [
            {
                "name": "wdio-regression",
                "cwd": "tests/wdio",
                "command": ["npm", "run", "wdio", "--", "--speckind", "regression"],
            }
        ],
    }


def parse_custom_command(command: str, cwd: str = ".", name: str = "custom") -> list[dict[str, Any]]:
    return [{"name": name, "cwd": cwd, "command": shlex.split(command)}]


def merge_pipelines(custom: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Dict[str, List[Dict[str, Any]]]:
    merged = default_pipelines()
    if custom:
        merged.update(custom)
    return merged
