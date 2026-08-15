## 1. What the Console Adds

<p class="lead">The top of this reader now includes the missing operator views: approval queue, running-now status, last runs, next runs, receipt browser, failure view, dispatcher health, and SHA evidence.</p>

<aside class="callout control">
<strong>Public-safe rule</strong>
<p>The browser can generate drafts and show redacted status. The private control repository is the authority for real enable/disable state, approvals, releases, and receipts.</p>
</aside>

## 2. Approval Model

An approval is not a note. It is a structured object in the private control repository. A real enablement must identify the job, requested state, approver, approval reference, approved commit SHA, and effective state.

```json
{
  "schema_version": "1.0",
  "approval_id": "APPROVAL-EXAMPLE-0001",
  "change_type": "job-enabled-state",
  "job_id": "example-daily-inventory",
  "requested_enabled_state": true,
  "approval_status": "draft-example",
  "requires_private_control_repo_commit": true
}
```

## 3. Runtime State Model

Runtime state answers what is running now, what ran last, what is scheduled next, and what failed. In the current setup execution is disabled, so the running-now table is intentionally empty.

| Runtime view | Source path in private control repo | Public result now |
|---|---|---|
| Dispatcher health | `status/dispatcher.json` | Not deployed |
| Running now | `status/running.json` | 0 jobs |
| Last runs | `status/last-runs.json` | Not run / execution disabled |
| Next runs | `status/next-runs.json` | None while disabled |
| Failures | `status/failures.json` | 0 failures |
| Receipts | `receipts/` | Example receipt only |

## 4. Receipt Model

A receipt proves what happened. Every future execution should record job id, server id, scheduled slot, actual start, finish, result, active control commit, active script hash, and output hash.

## 5. Repository Split

| Repo | Role | Holds |
|---|---|---|
| `ITOPS-IaT-Storage-Orchestrator` | Controlled reader / SOP-style public-safe docs | Explanation, redacted status, draft tools |
| `ITOPS-IaT-Operations-Console-Template` | Reusable operator console template | Inventory, create, view, approval, receipt UI pattern |
| `ITOPS-IaT-Storage-Orchestrator-Control` | Private desired-state authority | Real servers, jobs, scripts, approvals, releases, receipts, status |

## 6. Python and GitOps Support Boundary

<aside class="support-boundary-red">
<strong>Required support boundary</strong>
<p>If you are not familiar with Python or the Python runtime used by this repository, contact <code>StoragePythonTeam@</code> before editing scripts, builders, dispatchers, validators, or generated publication logic.</p>
<p>If you are not familiar with Git, GitHub, GitHub Enterprise, or GitOps, contact <code>StorageGitOPSTeam@</code> before editing orchestration, repository-control, schedule, branch, Pages, or release content.</p>
</aside>

## 7. Current Operating State

| Control | Current value |
|---|---|
| Execution enabled | No |
| Dispatcher installed | No |
| Server mutation | No |
| Jobs enabled | 0 |
| Running now | 0 |
| Approval queue | Draft example only |
| Receipts | Example not-run receipt only |

## 8. Next Implementation Step

The next implementation step is private only: replace placeholders in the private control repository with real server and job records, keep all jobs disabled, and require approval records before any future runner reads the repo.
