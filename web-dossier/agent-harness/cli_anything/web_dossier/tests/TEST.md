# TEST.md — cli-anything-web-dossier

## Part 1: Test Plan

### Test Inventory Plan
- `test_core.py`: 12 unit tests planned
- `test_full_e2e.py`: 6 E2E/subprocess tests planned

### Unit Test Plan
- `core/project.py`
  - Validate source markers
  - Create/save/load project roundtrip
  - Project info shape
  - Edge cases: missing required paths
- `core/session.py`
  - Set source/project state
  - Undo/redo behavior
  - Save/load session persistence
- `core/pipeline.py`
  - Default pipeline availability
  - Custom command parsing
- `utils/web_dossier_backend.py`
  - Dry-run command execution
  - Runtime execution with local shell command

### E2E Test Plan
- Installable CLI entrypoint works via subprocess
- JSON output contract for `doctor`, `project init`, `pipeline list`
- `run command` executes a real command (`python -c`) and returns captured output
- Project+source state flows across commands using project file

### Realistic Workflow Scenarios
- Workflow name: Project bootstrap
  - Simulates: Team member onboarding a local repo into harness
  - Operations chained: `project init -> project info -> pipeline list`
  - Verified: project file created, source path persisted, pipelines listed
- Workflow name: Safe execution preview
  - Simulates: CI operator validating command before run
  - Operations chained: `run command --dry-run -- <cmd>`
  - Verified: command metadata generated, no side effects
- Workflow name: Real command execution
  - Simulates: one-off diagnostics in repo context
  - Operations chained: `run command -- python -c ...`
  - Verified: return code, stdout, elapsed time, artifact output

## Part 2: Test Results

Pending execution.

### Executed Command

```bash
python3 -m pytest cli_anything/web_dossier/tests/ -v --tb=no
```

### Full Output

```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/xuyin/Documents/Repository/CLI-Anything/web-dossier/agent-harness
plugins: cov-7.0.0
collecting ... collected 17 items

cli_anything/web_dossier/tests/test_core.py::test_validate_source_path_success PASSED [  5%]
cli_anything/web_dossier/tests/test_core.py::test_validate_source_path_missing_markers PASSED [ 11%]
cli_anything/web_dossier/tests/test_core.py::test_project_roundtrip PASSED [ 17%]
cli_anything/web_dossier/tests/test_core.py::test_project_info PASSED    [ 23%]
cli_anything/web_dossier/tests/test_core.py::test_session_set_and_undo_redo PASSED [ 29%]
cli_anything/web_dossier/tests/test_core.py::test_session_save_load PASSED [ 35%]
cli_anything/web_dossier/tests/test_core.py::test_default_pipelines_have_expected_keys PASSED [ 41%]
cli_anything/web_dossier/tests/test_core.py::test_parse_custom_command PASSED [ 47%]
cli_anything/web_dossier/tests/test_core.py::test_backend_run_command_dry_run PASSED [ 52%]
cli_anything/web_dossier/tests/test_core.py::test_backend_run_pipeline_real_command PASSED [ 58%]
cli_anything/web_dossier/tests/test_core.py::test_backend_doctor_shape PASSED [ 64%]
cli_anything/web_dossier/tests/test_full_e2e.py::TestCLISubprocess::test_help PASSED [ 70%]
cli_anything/web_dossier/tests/test_full_e2e.py::TestCLISubprocess::test_doctor_json PASSED [ 76%]
cli_anything/web_dossier/tests/test_full_e2e.py::TestCLISubprocess::test_project_init_and_info PASSED [ 82%]
cli_anything/web_dossier/tests/test_full_e2e.py::TestCLISubprocess::test_pipeline_list_from_project PASSED [ 88%]
cli_anything/web_dossier/tests/test_full_e2e.py::TestCLISubprocess::test_run_command_dry_run PASSED [ 94%]
cli_anything/web_dossier/tests/test_full_e2e.py::TestCLISubprocess::test_run_command_real_execution PASSED [100%]

============================== 17 passed in 1.62s ==============================
```

### Summary Statistics
- Total tests: 17
- Passed: 17
- Failed: 0
- Pass rate: 100%
- Duration: 1.62s

### Coverage Notes
- Covered: project lifecycle, session undo/redo, pipeline resolution, backend execution, subprocess CLI JSON contracts.
- Not covered: full real `ant`/`npm` build and test pipelines on a production web-dossier environment.
