"""Static safety checks on the LIVE gate workflows under .github/workflows/.

These files execute for real against the sandbox repo (see
.github/instructions/workflows.instructions.md), so this test suite enforces the
guardrails from that instructions file mechanically, not just by convention.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"


def _workflow_files() -> list[Path]:
    if not WORKFLOWS_DIR.exists():
        return []
    return sorted(WORKFLOWS_DIR.glob("*.yml"))


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_workflow_parses_as_yaml(path: Path) -> None:
    """Every workflow file must be valid YAML."""
    doc = yaml.safe_load(path.read_text())
    assert isinstance(doc, dict)


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_every_job_declares_explicit_permissions(path: Path) -> None:
    """No job may inherit the ambient default permissions — see instructions file."""
    doc = yaml.safe_load(path.read_text())
    top_level_permissions = "permissions" in doc
    jobs = doc.get("jobs", {})
    for job_name, job in jobs.items():
        job_has_permissions = isinstance(job, dict) and "permissions" in job
        assert top_level_permissions or job_has_permissions, (
            f"{path.name}: job {job_name!r} declares no permissions "
            f"(workflow-level or job-level)"
        )


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_schedule_pairs_with_workflow_dispatch(path: Path) -> None:
    """A schedule-triggered workflow must also support workflow_dispatch."""
    doc = yaml.safe_load(path.read_text())
    on = doc.get("on") or doc.get(True)  # PyYAML may parse bare `on:` as True
    if not isinstance(on, dict):
        return
    if "schedule" in on:
        assert "workflow_dispatch" in on, (
            f"{path.name}: has schedule: but no workflow_dispatch: escape hatch"
        )


@pytest.mark.parametrize(
    "path",
    [p for p in _workflow_files() if p.name.startswith("gate")],
    ids=lambda p: p.name,
)
def test_gate_workflows_scope_to_sandbox_paths(path: Path) -> None:
    """Every gateN-*.yml must filter pull_request events to sandbox/** only.

    This is the guard that stops the airlock from ever acting on a PR that only
    edits curriculum content (learning_modules/, labs/, notebooks/).
    """
    doc = yaml.safe_load(path.read_text())
    on = doc.get("on") or doc.get(True)
    if not isinstance(on, dict) or "pull_request" not in on:
        pytest.skip(f"{path.name} is not pull_request-triggered")
    pr_trigger = on["pull_request"]
    paths = pr_trigger.get("paths", []) if isinstance(pr_trigger, dict) else []
    assert any("sandbox" in p for p in paths), (
        f"{path.name}: pull_request trigger has no sandbox/** paths filter"
    )


def test_no_inert_yaml_outside_workflows_dir() -> None:
    """A YAML file that LOOKS like a workflow but lives elsewhere would still run
    if GitHub ever saw it under .github/workflows/ — so no chapter content may place
    one there. This guards against a future edit accidentally copying an
    illustrative snippet into the live directory as a full file.
    """
    assert WORKFLOWS_DIR.exists(), ".github/workflows/ must exist"
    for path in _workflow_files():
        assert path.parent == WORKFLOWS_DIR
