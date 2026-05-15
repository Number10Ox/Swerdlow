"""End-to-end smoke test: init → bootstrap → apply → context."""
import shutil
import subprocess
import sys
from pathlib import Path


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "swerdlow", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_full_workflow(fixture_dir, tmp_path):
    # 1. Copy starter corpus.
    project = tmp_path / "ctxdrift"
    shutil.copytree(fixture_dir / "e2e", project)

    # 2. swerdlow init
    r = _run(["init"], cwd=project)
    assert r.returncode == 0
    cfg = project / ".swerdlow" / "config.yaml"
    # Tweak include so it matches our docs/ structure (default is Docs/, lowercase here).
    cfg.write_text('include:\n  - "docs/**/*.md"\n')

    # 3. swerdlow bootstrap
    r = _run(["bootstrap"], cwd=project)
    assert r.returncode == 0
    plan_path = project / ".swerdlow" / "bootstrap.plan.yaml"
    assert plan_path.exists()
    plan_text = plan_path.read_text()
    assert "GDD.md" in plan_text
    assert "Combat.md" in plan_text

    # 4. swerdlow bootstrap --apply
    r = _run(["bootstrap", "--apply"], cwd=project)
    assert r.returncode == 0

    # 5. swerdlow context Combat
    r = _run(["context", "Combat"], cwd=project)
    assert r.returncode == 0
    lines = r.stdout.strip().split("\n")
    names = [Path(p).name for p in lines]
    assert names[-1] == "Combat.md"
    assert "GDD.md" in names
    assert "GamePillars.md" in names


def test_v02_full_workflow_with_typed_edges(fixture_dir, tmp_path):
    """init → bootstrap → enrich plan with when: tags → apply → context --for."""
    project = tmp_path / "v02"
    shutil.copytree(fixture_dir / "e2e-v0.2", project)

    # 1. init
    r = _run(["init"], cwd=project)
    assert r.returncode == 0
    (project / ".swerdlow" / "config.yaml").write_text('include:\n  - "docs/**/*.md"\n')

    # 2. bootstrap
    r = _run(["bootstrap"], cwd=project)
    assert r.returncode == 0

    # 3. simulate the human enrichment step: edit the plan to add `when:` annotations.
    import yaml
    plan_path = project / ".swerdlow" / "bootstrap.plan.yaml"
    plan_data = yaml.safe_load(plan_path.read_text())

    # Find the proposal for Root.md and annotate its deps.
    for prop in plan_data["proposals"]:
        if prop["file"].endswith("Root.md"):
            new_deps = []
            for d in prop["add_depends_on"]:
                if d == "Hub":
                    new_deps.append({"id": "Hub", "when": ["narration"]})
                else:
                    new_deps.append(d)  # keep Leaf as bare-string (always)
            prop["add_depends_on"] = new_deps

    plan_path.write_text(yaml.safe_dump(plan_data, sort_keys=False))

    # 4. apply
    r = _run(["bootstrap", "--apply"], cwd=project)
    assert r.returncode == 0

    # 5. context Root --for narration → Hub IS in the bundle (narration matched).
    r = _run(["context", "Root", "--for", "narration"], cwd=project)
    assert r.returncode == 0
    names = {Path(p).name for p in r.stdout.strip().split("\n")}
    assert "Root.md" in names
    assert "Hub.md" in names
    assert "Leaf.md" in names  # always-edge to Leaf

    # 6. context Root --for design → Hub is NOT in bundle (narration filter cuts it).
    r = _run(["context", "Root", "--for", "design"], cwd=project)
    assert r.returncode == 0
    names = {Path(p).name for p in r.stdout.strip().split("\n")}
    assert "Hub.md" not in names
    assert "Root.md" in names
    assert "Leaf.md" in names  # always-edge survives any filter

    # 7. swerdlow modes shows narration as a present mode.
    r = _run(["modes"], cwd=project)
    assert r.returncode == 0
    assert "narration" in r.stdout
