"""Read and write the bootstrap plan YAML file."""
from pathlib import Path

import yaml

from swerdlow.types import BootstrapIssue, BootstrapPlan, Proposal

PLAN_FILENAME = "bootstrap.plan.yaml"


def write_plan(plan: BootstrapPlan, path: Path, force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(
            f"{path} already exists. Delete it or pass force=True to regenerate."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "proposals": [
            {"file": str(p.file), "add_depends_on": list(p.add_depends_on)}
            for p in plan.proposals
        ],
        "issues": [
            {"file": str(i.file), "link": i.link, "detail": i.detail}
            for i in plan.issues
        ],
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False, default_flow_style=False))


def load_plan(path: Path) -> BootstrapPlan:
    raw = yaml.safe_load(path.read_text()) or {}
    proposals = [
        Proposal(file=Path(p["file"]), add_depends_on=list(p.get("add_depends_on", [])))
        for p in (raw.get("proposals") or [])
    ]
    issues = [
        BootstrapIssue(file=Path(i["file"]), link=i["link"], detail=i["detail"])
        for i in (raw.get("issues") or [])
    ]
    return BootstrapPlan(proposals=proposals, issues=issues)
