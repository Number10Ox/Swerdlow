"""Tests for swerdlow.bootstrap.plan — (de)serialize BootstrapPlan to YAML."""
from pathlib import Path

import pytest

from swerdlow.bootstrap.plan import PLAN_FILENAME, load_plan, write_plan
from swerdlow.types import BootstrapIssue, BootstrapPlan, Proposal


def test_write_and_read_roundtrip(tmp_path):
    plan = BootstrapPlan(
        proposals=[Proposal(file=Path("Docs/Mission.md"), add_depends_on=["Pillars", "TDD"])],
        issues=[BootstrapIssue(file=Path("Docs/Signal.md"), link="../old.md", detail="outside corpus")],
    )
    plan_path = tmp_path / ".swerdlow" / "bootstrap.plan.yaml"
    plan_path.parent.mkdir(parents=True)
    write_plan(plan, plan_path)
    loaded = load_plan(plan_path)
    assert loaded.proposals == plan.proposals
    assert loaded.issues == plan.issues


def test_plan_filename_constant():
    assert PLAN_FILENAME == "bootstrap.plan.yaml"


def test_write_refuses_existing_without_force(tmp_path):
    plan_path = tmp_path / "p.yaml"
    plan_path.write_text("existing\n")
    with pytest.raises(FileExistsError):
        write_plan(BootstrapPlan(), plan_path)


def test_write_with_force_overwrites(tmp_path):
    plan_path = tmp_path / "p.yaml"
    plan_path.write_text("existing\n")
    write_plan(BootstrapPlan(), plan_path, force=True)
    # File now contains valid YAML, not "existing"
    assert "existing" not in plan_path.read_text()


def test_load_plan_empty_file(tmp_path):
    plan_path = tmp_path / "p.yaml"
    plan_path.write_text("proposals: []\nissues: []\n")
    plan = load_plan(plan_path)
    assert plan.proposals == []
    assert plan.issues == []


def test_plan_roundtrip_heterogeneous_add_depends_on(tmp_path):
    """add_depends_on can contain bare strings AND dict-form entries."""
    plan = BootstrapPlan(
        proposals=[
            Proposal(
                file=Path("Docs/Mission.md"),
                add_depends_on=[
                    "BareForm",
                    {"id": "DictForm", "when": ["narration"]},
                ],
            )
        ],
        issues=[],
    )
    plan_path = tmp_path / ".swerdlow" / "bootstrap.plan.yaml"
    plan_path.parent.mkdir(parents=True)
    write_plan(plan, plan_path)
    loaded = load_plan(plan_path)
    p = loaded.proposals[0]
    assert p.add_depends_on == [
        "BareForm",
        {"id": "DictForm", "when": ["narration"]},
    ]
