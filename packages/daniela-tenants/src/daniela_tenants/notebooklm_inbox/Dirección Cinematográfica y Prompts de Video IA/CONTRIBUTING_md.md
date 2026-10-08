### Contributing — aig-MONOREPO

Review standards live in docs/CODE-REVIEW.md. This file is the workflow.

#### Workflow

1. Branch from main: feat/
2. Keep PRs small (<400 lines) and single-concern.
3. Fill the PR template, including test evidence.
4. Green local gates required (no CI: Actions OFF by owner decision) — secret-guard, ruff on changed files, pytest.
5. Merge via squash. No direct pushes to main.

#### Commit style

#### Local gates (run before pushing)

```
# one-time setup
pip install pre-commit gitleaks
pre-commit install
git config core.hooksPath githooks   # local pre-push safe gate (opt-in)

# per change
git diff --name-only | grep '\.py$' | xargs ruff check
git diff --name-only | grep '\.py$' | xargs ruff format --check
pytest tests/ -m "not network and not android" -q
gitleaks protect --staged --verbose   # never skip this one
```

#### What reviewers (and CI) block on

P0 items from docs/CODE-REVIEW.md §2: secrets in diff, injection flaws, auth bypasses, data-loss paths, failing gates. When in doubt, ask in the PR — don't merge red.