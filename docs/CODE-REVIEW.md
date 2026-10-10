# Code Review Standards — aig-MONOREPO

> Humans review logic, security, and design. Machines review style.
> If a machine can check it, it must be automated — never spend human
> review time on it. Related: `CONTRIBUTING.md`, `CODEOWNERS`,
> `.github/pull_request_template.md`, `.pre-commit-config.yaml`.

## 1. Principles

1. **Review the change, not the author.** Comment on code, propose alternatives.
2. **Small PRs get fast reviews.** Target <400 changed lines. Above that the
   author must split or justify (refactors, vendored code, generated files).
3. **Approval means shared ownership.** If it breaks, author + reviewer fix it.
4. **Blocking comments are bugs, not opinions.** Anything blocking must cite a
   standard, a failing gate, or a concrete failure scenario.

## 2. Severity (every review comment carries one)

| Tag | Meaning | Example |
|---|---|---|
| `P0` | Blocker. Must fix before merge. | Secret/credential in diff, SQL/command injection, auth bypass, data-loss path, failing gate |
| `P1` | Should fix before merge (or tracked issue). | Missing test for new behavior, unhandled error path, N+1 query, breaking API change without migration |
| `P2` | Nit / follow-up. Never blocks. | Naming, comment wording, minor duplication, style a linter could learn |

Rules: at most one round of P2s per PR. P1s filed as issues must reference
the PR number. No "LGTM with 15 P2s" — batch nits or drop them.

## 3. Author checklist (must be true before requesting review)

- [ ] PR follows the template (what/why/risk/test evidence).
- [ ] Scope is one thing. No drive-by refactors.
- [ ] New behavior has tests; bugfix has a regression test.
- [ ] No secrets, `.env` dumps, `.db`, or PII in the diff
      (`git diff --stat` + `gitleaks protect --staged` clean).
- [ ] Local gates pass: `ruff check` + `ruff format --check` on changed
      files, `pytest tests/`.
- [ ] Quality ratchet not worsened (see §7).

## 4. Reviewer checklist

1. **Correctness first:** does it do what the description claims? Trace the
   main path + one error path by hand.
2. **Security:** new inputs (HTTP, files, env, subprocess, SQL)? Check
   injection, auth coverage (`aig_shared.auth` on every new `/api/*`),
   secret handling (vault/env, never literals).
3. **Tests as evidence:** would the tests fail if the fix were reverted?
   (Mutation sniff-test: if unsure, ask the author.)
4. **Scope & size:** unrelated changes → ask to split. >400 lines → ask why.
5. **No scope creep in review:** don't redesign the feature; file P1/P2.
6. **Docs/config:** new service, port, or env var? Must update
   `config/docker-compose*.yml`, `nginx.conf`, and `docs/` accordingly.

## 5. PR size guide

| Size | Lines changed | Expectation |
|---|---|---|
| XS/S | <200 | Review <4h, often same-day merge |
| M | 200–400 | Review <24h |
| L | 400–1000 | Requires justification; reviewer may demand split |
| XL | >1000 | Split, unless mechanical (renames, vendoring, generated) |

## 6. Review SLOs

- First review (approve or P0/P1 list): **<24h** for S/M, **<48h** for L.
- Author re-review turnaround: **<24h**.
- Stale PR (>7 days without activity): author closes or rebases + re-requests.

## 7. Automation (what runs, where, blocking?)

> 2026-09-23: GitHub Actions OFF by owner decision (zero billing).
> `.github/workflows/` is empty; `gitleaks`, ruff and pytest run LOCALLY
> via pre-commit + the pre-push gate. If Actions ever return, re-add
> `secret-scan`, `changed-lint` and `tests` as required checks (history
> has the workflow in commit `64b2857` and earlier).

| Gate | Where | Blocking? | Notes |
|---|---|---|---|
| Secret scan (gitleaks) | pre-commit + pre-push gate | **YES** | Non-negotiable after the 2026-09 secret incidents |
| Ruff on changed files | pre-commit + local | **YES** | `git diff --name-only \| grep '\.py$' \| xargs ruff check` |
| Tests (`pytest tests/`) | local (`pytest tests/`) | **YES** | |
| Full-repo ruff ratchet | local | **YES on increase** | Count in `.quality-baseline/ruff-count.txt` (valor vivo en el fichero) must not grow; lower it when you fix legacy code |
| Full ruff + mypy | local | Advisory | Informational until legacy debt is paid down |
| CodeQL | OFF with Actions | — | Re-enable with Actions if billing returns |

Why a ratchet instead of zero-tolerance: el repo llego a 0 findings el 2026-10-04
findings. Blocking on zero would freeze all work; blocking on *increase*
keeps every PR from adding debt while legacy is paid down file by file.

## 8. Branch protection (one-time setup, repo admin)

> Status 2026-09-23: **blocked by plan** — private repo on GitHub Free
> rejects the protection API (HTTP 403, requires Pro or public repo).
> Until upgraded: enforce by discipline (no direct pushes to `main`,
> CODEOWNERS still auto-assigns reviewers on PRs). Then apply below.

```bash
# Require PRs + the three blocking checks on main (GitHub CLI):
gh api repos/aig/aig-MONOREPO/branches/main/protection -X PUT \
  -f required_status_checks[strict]=true \
  -f required_status_checks[checks][][context]='secret-scan' \
  -f required_status_checks[checks][][context]='changed-lint' \
  -f required_status_checks[checks][][context]='tests' \
  -f enforce_admins=true \
  -f required_pull_request_reviews[required_approving_review_count]=1 \
  -f restrictions=null
```

Or UI: Settings → Branches → Add rule → `main` → Require pull request
before merging (1 approval) + Require status checks (secret-scan,
changed-lint, tests) + Do not allow bypassing.

## 9. Solo-dev protocol (current state: one maintainer)

Automation is the second reviewer. Additionally:

- **Risky changes** (auth, migrations, history rewrites, prod compose,
  secrets handling): self-review with a 24h gap — open PR, review next day.
- **Routine changes**: same-day self-review using §4 as a literal checklist
  in the PR description.
- **External review triggers** (get a second human before merge): new crypto,
  new network-exposed endpoints, `git filter-repo`, infra billing changes.

## 10. Metrics (review monthly, 15 min)

- Median time to first review vs §6 SLOs.
- P0 escape rate: blockers found post-merge (target: 0).
- Ratchet trend: `ruff-count.txt` over time (must slope down).
- Skipped-test count (must not grow without `network`/`android` reason).
