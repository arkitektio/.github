"""Bring one repo to the arkitekt Python standard, or check that it is there.

    uv run --with tomlkit python python/sync_quality.py <repo>            # write
    uv run --with tomlkit python python/sync_quality.py <repo> --check    # report drift, exit 1 on any

What the standard owns in a repo (rewritten on every sync):

- ``ruff.shared.toml`` and ``pyright.shared.json``: verbatim copies of this folder's.
- ``ruff`` and ``basedpyright`` in the ``dev`` dependency group, pinned to the
  versions below (the lockfile then decides what CI runs; run ``uv lock`` after).
- ``.github/workflows/quality.yaml``: a call to the shared ``python-quality``
  workflow, which replaces the repo's own ``lint.yaml`` / ``typecheck.yaml``.

What the repo owns (made once, from its old settings, then left alone):

- ``ruff.toml``: ``extend = "ruff.shared.toml"`` plus its target version,
  excludes (vendored code) and per-file ignores.
- ``pyrightconfig.json``: ``"extends": "./pyright.shared.json"`` plus what to check.

The old ``[tool.ruff]``, ``[tool.basedpyright]``, ``[tool.pyright]`` and
``[tool.mypy]`` sections are removed: a ``ruff.toml`` / ``pyrightconfig.json``
would silently win over them anyway.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import tomlkit
from tomlkit.container import OutOfOrderTableProxy
from tomlkit.items import Array, Table

RUFF_VERSION = "0.17.6"
BASEDPYRIGHT_VERSION = "1.40.2"

HERE = Path(__file__).resolve().parent
SHARED_FILES = ("ruff.shared.toml", "pyright.shared.json")
OLD_WORKFLOWS = ("lint.yaml", "lint.yml", "typecheck.yaml", "typecheck.yml")
#: What `document["tool"]` is: a Table, or a proxy when `[tool.*]` tables are split
#: across the file (another table between them).
TOOL_TYPES = (Table, OutOfOrderTableProxy)
OLD_SECTIONS = ("ruff", "basedpyright", "pyright", "mypy", "django-stubs")


def quality_workflow(python_version: str, sync_args: str | None = None) -> str:
    extra = f'\n      sync-args: "{sync_args}"' if sync_args else ""
    return f"""name: Quality

# The arkitekt Python standard: ruff lint, ruff format and basedpyright (against
# .basedpyright/baseline.json), all required. Owned by arkitektio/.github
# (python/sync_quality.py writes this file); the settings are ruff.toml and
# pyrightconfig.json, which extend the shared ones.

on:
  push:
    branches: [main, next]
  pull_request:
    branches: [main, next]
  workflow_dispatch: {{}}

jobs:
  quality:
    uses: arkitektio/.github/.github/workflows/python-quality.yml@main
    with:
      python-version: "{python_version}"{extra}
"""


def sync_args_of(workflow: Path) -> str | None:
    """A repo's own `sync-args` (e.g. a group a typecheck needs): kept across syncs."""
    if not workflow.exists():
        return None
    found = re.search(r'^\s+sync-args:\s*"([^"]*)"', workflow.read_text(), re.MULTILINE)
    return found.group(1) if found else None


def python_version_of(repo: Path, project: dict[str, object]) -> str:
    pinned = repo / ".python-version"
    if pinned.exists():
        return pinned.read_text().strip()
    requires = str(project.get("requires-python", ""))
    found = re.search(r"3\.(\d+)", requires)
    return f"3.{max(12, int(found.group(1)))}" if found else "3.12"


def target_version_of(project: dict[str, object]) -> str:
    found = re.search(r"3\.(\d+)", str(project.get("requires-python", "")))
    return f"py3{found.group(1)}" if found else "py312"


def initial_ruff_toml(old: dict[str, object], project: dict[str, object]) -> str:
    excludes = ruff_excludes_of(old)
    lines = [
        "# This repo's ruff settings: the arkitekt standard (ruff.shared.toml, synced",
        "# from arkitektio/.github) plus what is this repo's own. Add excludes for",
        "# vendored code and per-file ignores here; never edit ruff.shared.toml.",
        'extend = "ruff.shared.toml"',
        f'target-version = "{target_version_of(project)}"',
    ]
    if excludes:
        lines.append("extend-exclude = [")
        lines.extend(f'  "{item}",' for item in excludes)
        lines.append("]")
    return "\n".join(lines) + "\n"


#: Never type-checked: generated, installed or cached.
ALWAYS_EXCLUDED = [
    "**/migrations",
    "**/__pycache__",
    "**/node_modules",
    ".venv",
    "build",
    "dist",
]


def initial_pyrightconfig(old: dict[str, object], ruff_excludes: list[str]) -> str:
    """What the repo checked before, or else everything but what ruff skips too."""
    include = old.get("include")
    exclude = old.get("exclude")
    config: dict[str, object] = {
        "extends": "./pyright.shared.json",
        "include": list(include) if isinstance(include, list) and include else ["."],
        "exclude": list(
            dict.fromkeys(
                [
                    *ALWAYS_EXCLUDED,
                    *(exclude if isinstance(exclude, list) else []),
                    *ruff_excludes,
                ]
            )
        ),
    }
    return json.dumps(config, indent=2) + "\n"


def ruff_excludes_of(old: dict[str, object]) -> list[str]:
    excludes: list[str] = []
    for key in ("exclude", "extend-exclude"):
        value = old.get(key)
        if isinstance(value, list):
            excludes.extend(str(item) for item in value if str(item) not in excludes)
    return excludes


def pin_dev_group(document: tomlkit.TOMLDocument) -> bool:
    """Pin ruff and basedpyright in the `dev` group; True when anything changed."""
    groups = document.get("dependency-groups")
    if groups is None:
        groups = tomlkit.table()
        document["dependency-groups"] = groups
    dev = groups.get("dev")
    if dev is None:
        dev = tomlkit.array()
        dev.multiline(True)
        groups["dev"] = dev
    assert isinstance(dev, Array)
    wanted = {
        "ruff": f"ruff=={RUFF_VERSION}",
        "basedpyright": f"basedpyright=={BASEDPYRIGHT_VERSION}",
    }
    changed = False
    for name, spec in wanted.items():
        matches = [
            index
            for index, item in enumerate(dev)
            if re.match(rf"{name}\b(?![-_])", str(item))
        ]
        if matches and [str(dev[index]) for index in matches] == [spec]:
            continue
        changed = True
        if not matches:
            dev.append(spec)
            continue
        # In place, so a comment above the old entry stays with it.
        dev[matches[0]] = spec
        for index in reversed(matches[1:]):
            del dev[index]
    return changed


def _without_tool_section(
    document: tomlkit.TOMLDocument, section: str
) -> tomlkit.TOMLDocument:
    """`document` without `[tool.<section>]` (and without `[tool]` once it is empty)."""
    fresh = tomlkit.parse(tomlkit.dumps(document))
    tool = fresh.get("tool")
    if isinstance(tool, TOOL_TYPES) and section in tool:
        del tool[section]
        if len(fresh["tool"]) == 0:
            del fresh["tool"]
    return fresh


def sync(repo: Path, check: bool) -> list[str]:
    drift: list[str] = []
    pyproject_path = repo / "pyproject.toml"
    document = tomlkit.parse(pyproject_path.read_text())
    project = dict(document.get("project", {}))
    tool = document.get("tool")
    old_tool = dict(tool) if isinstance(tool, TOOL_TYPES) else {}

    for name in SHARED_FILES:
        source, target = HERE / name, repo / name
        if not target.exists() or target.read_bytes() != source.read_bytes():
            drift.append(f"{name} differs from the standard")
            if not check:
                shutil.copyfile(source, target)

    if not (repo / "ruff.toml").exists():
        drift.append("ruff.toml missing")
        if not check:
            old_ruff = old_tool.get("ruff", {})
            (repo / "ruff.toml").write_text(
                initial_ruff_toml(dict(old_ruff) if old_ruff else {}, project)
            )

    if not (repo / "pyrightconfig.json").exists():
        drift.append("pyrightconfig.json missing")
        if not check:
            old_pyright = old_tool.get("basedpyright") or old_tool.get("pyright") or {}
            old_ruff = old_tool.get("ruff", {})
            excludes = ruff_excludes_of(dict(old_ruff) if old_ruff else {})
            (repo / "pyrightconfig.json").write_text(
                initial_pyrightconfig(dict(old_pyright), excludes)
            )

    # One section at a time, each on a fresh parse: tomlkit's proxy for split
    # `[tool.*]` tables goes stale after a delete.
    for section in OLD_SECTIONS:
        if section in old_tool:
            drift.append(f"[tool.{section}] still in pyproject.toml")
            if not check:
                document = _without_tool_section(document, section)

    if pin_dev_group(document):
        drift.append(
            f"dev group does not pin ruff=={RUFF_VERSION} / basedpyright=={BASEDPYRIGHT_VERSION}"
        )
    if not check:
        pyproject_path.write_text(tomlkit.dumps(document))

    workflows = repo / ".github" / "workflows"
    wanted = quality_workflow(
        python_version_of(repo, project),
        sync_args_of(workflows / "quality.yaml"),
    )
    target = workflows / "quality.yaml"
    if not target.exists() or target.read_text() != wanted:
        drift.append(".github/workflows/quality.yaml differs from the standard")
        if not check:
            workflows.mkdir(parents=True, exist_ok=True)
            target.write_text(wanted)
    for name in OLD_WORKFLOWS:
        if (workflows / name).exists():
            drift.append(f".github/workflows/{name} replaced by quality.yaml")
            if not check:
                (workflows / name).unlink()
    return drift


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("repo", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without writing; exit 1 on any",
    )
    args = parser.parse_args()
    repo = args.repo.resolve()
    drift = sync(repo, check=args.check)
    for line in drift:
        print(f"{repo.name}: {line}")
    if args.check:
        return 1 if drift else 0
    if drift:
        print(
            f"{repo.name}: synced; now run `uv lock`, `uv run ruff check --fix .`, `uv run ruff format .` and `uv run basedpyright --writebaseline`"
        )
    else:
        print(f"{repo.name}: already on the standard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
