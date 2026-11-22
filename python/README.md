# The arkitekt Python standard

One lint, format and type-check standard for every Python repo (servers and
client packages), checked by one reusable workflow.

| File | What it is |
|---|---|
| `ruff.shared.toml` | The shared ruff rules: correctness (F, E9, PLE, B, ASYNC, DTZ, LOG, T10, ISC), autofixable modernizations (I, UP), and ANN: every argument and return annotated, no `Any`. Line length 88, as Black. No docstring rules, no PEP 695 generic syntax, no `Self`. |
| `pyright.shared.json` | basedpyright in `standard` mode. |
| `sync_quality.py` | Brings a repo to the standard, or checks it is there (`--check`). |
| `../.github/workflows/python-quality.yml` | The reusable workflow: `ruff check`, `ruff format --check`, `basedpyright` against the repo's baseline. All required. |

## Adopting it in a repo

```sh
uv run --with tomlkit python <this repo>/python/sync_quality.py <repo>
cd <repo>
uv lock && uv sync --all-extras --dev
uv run ruff check --fix . && uv run ruff format .   # commit as `style:`, add the hash to .git-blame-ignore-revs
uv run ruff check .                                  # again: wrapping can move a `noqa` off its line
# fix what is left by hand (mostly annotations)       # commit as `fix:`
uv run basedpyright --writebaseline                   # commit with the workflow switch
```

A repo owns `ruff.toml` (`extend = "ruff.shared.toml"` plus excludes for
vendored code and per-file ignores) and `pyrightconfig.json`
(`"extends": "./pyright.shared.json"` plus what to check). It never edits the
two shared files: change them here and re-sync.

## The type-check baseline

`.basedpyright/baseline.json` lists the errors a repo had when it adopted the
standard. CI tolerates those and fails on any other. Fix one, run
`basedpyright --writebaseline`, and the baseline shrinks; it never grows back.
