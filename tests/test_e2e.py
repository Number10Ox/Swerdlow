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
