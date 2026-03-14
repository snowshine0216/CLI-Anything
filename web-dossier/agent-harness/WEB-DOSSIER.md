# web-dossier CLI Harness Analysis

## Target
- Source repository: `/Users/xuyin/Documents/Repository/web-dossier`
- Product: MicroStrategy Library (web-dossier)

## Backend Surfaces Mapped
- Build WAR (source build): `ant -f production/build/build.xml build-war`
- Build WAR (engineering shortcut): `production/build/build-war.sh`
- Integration tests (Playwright): `cd tests/integration && npm test`
- WDIO tests: `cd tests/wdio && npm run wdio -- <args>`
- PR handler lint: `cd pull-request/pullRequestHandler && npm run lint`

## Data/State Model
- Project file (`.web-dossier-cli.json`) stores:
  - `source_path`
  - named pipeline definitions
  - metadata timestamps
- Session file (`~/.cli-anything-web-dossier/session.json`) stores:
  - active source path
  - active project path
  - custom pipelines
  - undo/redo stack over session mutations

## CLI Design
- One-shot subcommands for automation
- REPL default mode when no subcommand is supplied
- JSON output via `--json`
- Pipeline execution wrapper that captures stdout/stderr/exit code and timing

## Hard Dependencies
- Python 3.10+
- `git` (repo checks)
- Optional but expected for real workflows:
  - `ant`
  - `node`/`npm`/`npx`

## Notes
- This harness wraps repository workflows and scripts. It does not reimplement web-dossier build/test behavior.
