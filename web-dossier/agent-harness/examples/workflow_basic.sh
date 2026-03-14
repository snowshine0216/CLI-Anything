#!/usr/bin/env bash
set -euo pipefail

SOURCE_PATH="${1:-/Users/xuyin/Documents/Repository/web-dossier}"
PROJECT_PATH="${2:-/tmp/web-dossier-cli.json}"

cli-anything-web-dossier project init --source "$SOURCE_PATH" -o "$PROJECT_PATH"
cli-anything-web-dossier --project "$PROJECT_PATH" pipeline list
cli-anything-web-dossier --project "$PROJECT_PATH" pipeline run build-war --dry-run
