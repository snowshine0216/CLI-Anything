# cli-anything-web-dossier

Stateful CLI harness for `web-dossier` repository workflows.

## What It Wraps
- WAR build workflows (`ant`, `build-war.sh`)
- Integration tests (`tests/integration`)
- WDIO tests (`tests/wdio`)
- Pull request handler linting

## Hard Dependencies
- Python 3.10+
- `git`
- For real build/test execution:
  - `ant`
  - `node`, `npm`, `npx`

## Install

```bash
cd web-dossier/agent-harness
pip install -e .
```

## Quick Start

```bash
# Initialize project file for existing web-dossier source
cli-anything-web-dossier project init \
  --source /Users/xuyin/Documents/Repository/web-dossier \
  -o /tmp/web-dossier-cli.json

# Validate source markers
cli-anything-web-dossier --project /tmp/web-dossier-cli.json project validate

# List available pipelines
cli-anything-web-dossier --project /tmp/web-dossier-cli.json pipeline list

# Dry-run build pipeline
cli-anything-web-dossier --project /tmp/web-dossier-cli.json pipeline run build-war --dry-run

# Enter REPL mode
cli-anything-web-dossier
```

## JSON Output

```bash
cli-anything-web-dossier --json doctor
```

## Tests

```bash
python3 -m pytest cli_anything/web_dossier/tests/ -v

# Force subprocess tests to use installed executable
CLI_ANYTHING_FORCE_INSTALLED=1 python3 -m pytest cli_anything/web_dossier/tests/test_full_e2e.py -v -s
```
