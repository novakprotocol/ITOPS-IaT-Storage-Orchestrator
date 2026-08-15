## 1. Control Center First

<p class="lead">The public documentation reader opens with the control-console concept: inventory, create job draft, view jobs, view servers, draft enable/disable, scripts, approvals, receipts, and then the long-form controlled document.</p>

<aside class="callout control">
<strong>Split-repository rule</strong>
<p>The documentation repository publishes a controlled reader and public-safe draft tools. The private control repository owns the real server registry, job registry, script inventory, approvals, releases, receipts, and enable/disable state.</p>
</aside>

## 2. Why the Split Exists

Operational sprawl happens when scripts, local timers, manual launch patterns, receipts, and small utility jobs grow across different servers without one reviewed source of truth. The resulting questions are basic but difficult to answer:

| Question | Required source of truth |
|---|---|
| Which server owns the job? | Private server registry |
| When should it run? | Private job schedule |
| What script is allowed? | Private script register |
| Who approved it? | Private approval record |
| What SHA authorized it? | Private release record |
| Did it run? | Receipt and status record |

## 3. Repository Responsibilities

| Repository | Purpose | Public or private |
|---|---|---|
| `ITOPS-IaT-Storage-Orchestrator` | Controlled documentation reader, public-safe console explanation, synthetic examples, and draft JSON generator. | Public-safe |
| `ITOPS-IaT-Operations-Console-Template` | Reusable operations-console template for inventory, create, view, enable/disable draft, scripts, approvals, and receipts. | Public-safe template |
| `ITOPS-IaT-Storage-Orchestrator-Control` | Real desired state: servers, jobs, scripts, schedules, approvals, receipts, release records, and sanitized exports. | Private |

## 4. Operations Console Pattern

The operations console template must put the active work surface at the top:

1. Inventory.
2. Create job draft.
3. View jobs.
4. View servers.
5. Draft enable/disable.
6. Scripts.
7. Approvals.
8. Receipts.
9. Controlled document.

The console can generate change JSON. It must not directly execute server-side work from a browser.

## 5. Enable and Disable Boundary

A visible enable/disable control is useful only as a draft generator. The real control is a reviewed private-repository commit.

```json
{
  "change_type": "job-enabled-state",
  "job_id": "example-daily-inventory",
  "old_enabled": false,
  "new_enabled": true,
  "requires_review": true,
  "requires_private_control_repo_commit": true
}
```

## 6. Private Control Repository Layout

```text
servers/
jobs/
scripts/
orchestrator/
schemas/
approvals/
releases/
receipts/
exports/public/
```

The future dispatcher reads the private control repository, not the public Pages site.

## 7. Python-Only Implementation Rule

<aside class="support-boundary-red">
<strong>Required support boundary</strong>
<p>If you are not familiar with Python or the Python runtime used by this repository, contact <code>StoragePythonTeam@</code> before editing scripts, builders, dispatchers, validators, or generated publication logic.</p>
<p>If you are not familiar with Git, GitHub, GitHub Enterprise, or GitOps, contact <code>StorageGitOPSTeam@</code> before editing orchestration, repository-control, schedule, branch, Pages, or release content.</p>
</aside>

PowerShell is not the implementation language for this repository pattern. Operational logic is Python-first.

## 8. Ansible Relationship

This is not an Ansible-based system. The foundation is Git-governed orchestration: server records, job records, schedules, policy, validation, dispatch, and receipts.

Ansible can become one optional executor lane later, especially for idempotent configuration tasks. It is not the control plane.

## 9. Approval and SHA Evidence

Every material change should identify:

| Evidence | Required value |
|---|---|
| Documentation source SHA | Commit in the public docs repository |
| Console template SHA | Commit in the operations-console template repository |
| Control source SHA | Commit in the private control repository |
| Approver | Person or role approving the change |
| Approval record | Pull request, issue, ticket, or controlled record |
| Effective state | Enabled or disabled |
| Rollback | Prior known-good SHA and restoration method |

## 10. Next Implementation Gates

- Build and publish the documentation reader.
- Create the operations-console template.
- Create the private Orchestrator control repository from the console template.
- Keep example jobs disabled.
- Add real private server and job data only to the private control repository.
- Add sanitized exports from the private repo to the public docs reader only after review.
