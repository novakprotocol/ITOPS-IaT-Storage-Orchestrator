## 1. Template Use and Document Profile Selection

<p class="lead">This is the reusable 2210-series document template. It is not an operational procedure and contains no system-specific authority.</p>

<aside class="callout template">
  <strong>Template instruction</strong>
  <p>Create a new private repository from this template, select the document profile, complete document control, replace all instructional text, remove unused optional modules, validate, review, approve, and then publish the controlled Pages site.</p>
</aside>

| Document profile | Use when the artifact must… | Typical required modules |
|---|---|---|
| SOP | Establish repeatable operational policy and responsibility. | Purpose, scope, authority, roles, procedure, evidence, review. |
| IOP | Define an internal operating method with controls and approvals. | Baseline, authorization, steps, verification, exceptions, audit. |
| MOP / Implementation Plan | Control a bounded change or maintenance event. | Preconditions, impact, steps, stop points, validation, rollback, communications. |
| Runbook / Playbook | Guide rapid diagnosis, response, restoration, or escalation. | Triggers, triage, decision branches, actions, validation, escalation, recovery. |
| Work Instruction | Explain a narrow technician task at execution level. | Prerequisites, numbered actions, expected results, evidence, checklist. |
| Technical Standard | Define mandatory technical rules or configuration baselines. | Authority, requirements, baseline, exceptions, validation, lifecycle. |
| System / Service Design | Describe architecture, interfaces, data flows, controls, and tradeoffs. | Requirements, architecture, components, dependencies, security, operations. |
| Test / Validation Plan | Prove that requirements and controls are satisfied. | Scope, environment, cases, pass criteria, defects, evidence, acceptance. |
| Recovery / Continuity Plan | Restore or sustain service during disruption. | Triggers, RTO/RPO, backups, failover, restoration, communications, exercises. |
| Training / Job Aid | Enable qualified performance and knowledge transfer. | Audience, objectives, prerequisites, lessons, exercises, assessment, references. |
| Governance / Catalog | Control definitions, ownership, lifecycle, or approved options. | Authority, schema, ownership, change process, quality, review. |
| Retirement / Decommission Plan | Remove a system or service without losing records or control. | Inventory, dependencies, approvals, migration, destruction, validation, closure. |

See `2210-DOCUMENT-PROFILES.md` and the `examples/` directory for profile-specific starting points.

<aside class="callout control">
  <strong>AI and automation contract</strong>
  <p>An AI, GPT, coding agent, or generator must read <code>AGENTS.md</code> and <code>ai/template-contract.json</code>, preserve the controlled reader shell, and create the requested artifact in a separate private derived repository. Visual similarity alone is not conformance.</p>
</aside>

## 2. Document Identity and Control

<p class="lead">Identify exactly what the document is, who owns it, who created it, what it supersedes, and when it must be reviewed.</p>

| Control field | Required content |
|---|---|
| Document ID | Stable identifier that does not change when the title changes. |
| Document profile / type | SOP, IOP, MOP, runbook, work instruction, standard, design, plan, training, catalog, or other approved profile. |
| Title and subtitle | Clear subject and controlled outcome. |
| Version and status | Draft, in review, approved, effective, superseded, retired, or other governed state. |
| Creator | Original creator, account, Work Ledger ID, position number, and creation date. |
| Owner and steward | Accountable organization and person/role maintaining the artifact. |
| Reviewer and approver | Required technical, operational, security, privacy, records, management, or owner concurrence. |
| Effective and review dates | Effective date, last review, next required review, and review cycle. |
| Classification / sensitivity | Approved marking and handling restrictions. |
| Source repository | Canonical GHE repository and branch. |
| Supersedes / related documents | Prior versions, dependent procedures, standards, designs, and records. |

<aside class="callout control">
  <strong>Single source of truth</strong>
  <p>The published Pages site is the controlled reading surface. Repository content, review, approval, revision, and release evidence remain the controlled editing source.</p>
</aside>

## 3. Executive Summary, Purpose, Objectives, and Expected Outcomes

<p class="lead">State why the artifact exists, what problem it controls, what outcome it must produce, and how success will be recognized.</p>

- **Purpose:** Replace with the exact operational or technical purpose.
- **Objective:** Replace with measurable objectives.
- **Expected outcome:** Replace with the intended service, control, or user result.
- **Business or mission value:** Replace with the supported mission need.
- **Non-goals:** State what the document does not attempt to authorize or solve.

## 4. Scope, Applicability, Assumptions, Constraints, and Exclusions

| Category | Controlled statement |
|---|---|
| Included systems / services | List platforms, applications, environments, sites, data, or service classes. |
| Included roles / users | Identify who may perform, approve, review, or consume the work. |
| Applicability triggers | Define events, schedules, thresholds, requests, or conditions that invoke the document. |
| Assumptions | Record assumptions that must be verified before use. |
| Constraints | Record technology, policy, staffing, time, access, funding, or environmental limits. |
| Exclusions | State what is governed elsewhere and link the controlling source. |
| Geographic / organizational boundary | Identify enterprise, district, division, facility, team, or service boundary. |

<aside class="callout stop">
  <strong>No silent scope</strong>
  <p>A familiar name, legacy practice, or prior configuration does not establish authority. Stop when ownership, applicability, or system-of-record scope is unresolved.</p>
</aside>

## 5. Authority, Policy, References, Standards, and Compliance Crosswalk

| Source | Requirement controlled | Applicability | Evidence / link |
|---|---|---|---|
| Law, regulation, policy, directive, or standard | Replace with the binding requirement. | State why it applies. | Record the authoritative location. |
| Technical standard or architecture decision | Replace with the design or configuration requirement. | Identify affected components. | Record version and owner. |
| ITSM, IAM, security, privacy, records, or owner authority | Replace with the approval boundary. | Identify decision rights. | Record the controlling system. |

Use this section to map NIST, Example, OMB, CISA, organizational, platform, vendor, records, privacy, accessibility, safety, labor, acquisition, or local requirements when applicable.

## 6. Definitions, Acronyms, Naming, Data Classification, and Controlled Terms

| Term / acronym | Controlled meaning | Source / owner |
|---|---|---|
| Replace term | Define the meaning used by this document. | Identify source or decision owner. |
| System of record | The authoritative source for a defined class of information. | Name the approved source. |
| Incomplete | A required action or verification could not be performed; it is not a passing result. | Document owner. |

Also define naming conventions, identifiers, status values, severity levels, environment names, data classifications, and units of measure.

## 7. Audience, Roles, Responsibilities, Qualifications, RACI, and Separation of Duties

| Role | Responsibility | Required qualification / access | Evidence |
|---|---|---|---|
| Process or service owner | Owns outcome, risk, scope, and document lifecycle. | Assigned authority. | Approval record. |
| Document steward | Maintains content, revisions, review dates, and source integrity. | Repository access and subject knowledge. | Revision history. |
| Implementer | Performs only authorized work and records results. | Current role, training, access, and duty status. | Execution evidence. |
| Peer reviewer | Independently verifies scope, method, and result. | Independence and technical competency. | Review disposition. |
| Approver | Accepts defined risk and authorizes release or execution. | Delegated approval authority. | Approval evidence. |

Add RACI, segregation-of-duties, on-call, escalation, vendor, contractor, records, privacy, security, and data-owner roles as required.

## 8. Service, System, Product, or Process Overview

<p class="lead">Provide enough context to understand the controlled environment without exposing credentials, sensitive endpoints, or unnecessary internal details.</p>

| Element | Description |
|---|---|
| Mission / service function | Describe what the service or process provides. |
| Users / consumers | Identify primary and dependent consumers. |
| Environments | Production, development, test, lab, recovery, or other approved environments. |
| Major components | Hardware, software, services, repositories, agents, interfaces, or teams. |
| Ownership boundary | Identify operational, application, infrastructure, security, vendor, and data boundaries. |

Include a sanitized architecture diagram, context diagram, swimlane, process flow, state model, or topology when it materially improves execution or review.

## 9. Architecture, Interfaces, Dependencies, Data Flows, and Integration Boundaries

| Component / interface | Direction | Protocol / method | Data / function | Owner | Failure effect |
|---|---|---|---|---|---|
| Replace component | Inbound / outbound / bidirectional | Replace | Replace | Replace | Replace |

Document upstream and downstream dependencies, authentication boundaries, trust zones, ports, APIs, queues, schedules, data flows, time synchronization, certificates, DNS, network, storage, compute, backup, monitoring, automation, and external services as applicable.

## 10. Inventory, Configuration Baseline, Parameters, Schemas, and Approved Options

| Item / parameter | Approved value or range | Source of truth | Validation method | Change authority |
|---|---|---|---|---|
| Replace item | Replace approved value. | Replace authoritative catalog or configuration source. | Replace check. | Replace role or process. |

Use this module for configuration baselines, environment variables, feature flags, firmware, software versions, device inventories, service accounts, ports, paths, naming, retention, schedules, data dictionaries, JSON/YAML schemas, and approved option catalogs.

## 11. Preconditions, Prerequisites, Access, Approvals, Maintenance Window, and Readiness

<aside class="callout warning">
  <strong>Do not begin until every applicable prerequisite passes</strong>
  <p>Missing authority, access, backup, rollback, dependency health, owner concurrence, or maintenance-window readiness is a stop condition.</p>
</aside>

| Prerequisite | Pass criterion | Evidence | Owner |
|---|---|---|---|
| Controlling record | Request, incident, problem, task, or change identifies scope and authority. | Record ID. | Request / change owner. |
| Qualified personnel | Training, role, access, and duty status are current. | Qualification evidence. | Supervisor. |
| Starting state | Health, configuration, capacity, alerts, backups, and dependencies are captured. | Before-state evidence. | Implementer. |
| Recovery readiness | Rollback or restoration is technically possible and tested as required. | Recovery evidence. | Technical owner. |
| Communications | Stakeholders and notification paths are identified. | Communications plan. | Coordinator. |

## 12. Risk, Impact, Safety, Privacy, Cybersecurity, and Change Assessment

| Risk / impact | Likelihood | Consequence | Control / mitigation | Owner | Residual disposition |
|---|---|---|---|---|---|
| Replace risk | Low / medium / high or approved scale. | Replace. | Replace. | Replace. | Accept / reduce / transfer / avoid. |

Consider service interruption, data loss, confidentiality, integrity, availability, privilege, privacy, records, accessibility, safety, staffing, schedule, cost, vendor, legal, labor, customer, and mission impacts.

## 13. Inputs, Outputs, Artifacts, Records, and Systems of Record

| Artifact / record | Input or output | Authoritative location | Required fields | Retention / handling |
|---|---|---|---|---|
| Controlling work record | Input and output | Approved ITSM source | Scope, approvals, actions, result, evidence. | Apply approved retention. |
| Before / after evidence | Output | Approved evidence location | Timestamp, object, tool/version, result, reviewer. | Do not include secrets. |
| Configuration update | Output | Approved configuration source | Versioned, attributable, reviewable change. | Follow source governance. |

## 14. Detailed Procedure, Tasks, Commands, Expected Results, and Evidence

<p class="lead">Write each action so a qualified 2210 technician can perform it without undocumented institutional knowledge.</p>

| Step | Action | Command / interface | Expected result | Evidence | Stop / branch |
|---:|---|---|---|---|---|
| 1 | Verify identity, scope, authority, and starting state. | Replace with approved interface or command. | Exact target and baseline are confirmed. | Before-state artifact. | Stop on mismatch. |
| 2 | Perform the authorized action. | Replace with sanitized command or UI path. | Defined state change occurs. | Execution record. | Follow decision ID if result differs. |
| 3 | Validate immediate health and intended result. | Replace with test. | Pass criteria are met. | Validation result. | Roll back or escalate on failure. |

<aside class="callout evidence">
  <strong>Evidence requirement</strong>
  <p>For each material step, identify what proves the action occurred, who performed it, when it occurred, what object was affected, and whether the result passed.</p>
</aside>

## 15. Decision Points, Branches, Stop Conditions, Hold Points, and Escalation

| Decision ID | Condition / observation | Action | Authority | Evidence |
|---|---|---|---|---|
| DEC-001 | Replace condition. | Continue, hold, branch, roll back, or escalate. | Replace role. | Decision record. |

<aside class="callout stop">
  <strong>Objective stop conditions</strong>
  <p>List exact technical, safety, security, ownership, approval, capacity, data, timing, or dependency conditions that require immediate stop, containment, notification, or rollback.</p>
</aside>

## 16. Validation, Testing, Acceptance, Quality Gates, and Independent Review

| Test / control ID | Requirement | Method | Pass criterion | Evidence | Reviewer |
|---|---|---|---|---|---|
| VAL-001 | Identity and scope | Resolve target against the authoritative source. | Every target matches the approved record. | Query or export. | Peer reviewer. |
| VAL-002 | Functional result | Execute representative functional test. | Intended result is demonstrated without new error. | Test record. | Service owner. |
| VAL-003 | Security / control result | Verify applicable control. | No unauthorized broadening, exposure, or unresolved exception. | Control evidence. | Security / technical reviewer. |

Include unit, integration, system, performance, security, accessibility, backup/restore, failover, user acceptance, regression, negative, rollback, and evidence-quality tests when applicable.

## 17. Rollback, Recovery, Contingency, Failover, and Restoration

| Trigger | Recovery action | Recovery point / source | Validation | Escalation |
|---|---|---|---|---|
| Replace failure or stop condition. | Replace exact recovery steps. | Snapshot, backup, previous configuration, alternate service, or manual process. | Replace restoration tests. | Replace role and contact path. |

State rollback limits, irreversible steps, data reconciliation, transaction handling, service re-entry, incident linkage, and conditions for abandoning rollback in favor of recovery.

## 18. Incident, Problem, Request, Task, and Change Integration

| Record type | When required | Minimum linkage | Closure criterion |
|---|---|---|---|
| Request / task | Routine authorized service work. | Requester, owner, target, entitlement, result. | Acceptance and evidence complete. |
| Change | Material configuration or service change. | Risk, impact, schedule, approvals, implementation, validation, rollback. | Change review complete. |
| Incident | Unplanned interruption or degradation. | Detection, impact, actions, restoration, communications. | Service restored and follow-up assigned. |
| Problem / known error | Recurring or root-cause work. | Evidence, root cause, workaround, corrective action. | Disposition approved. |

## 19. Monitoring, Logging, Alerting, Observability, Drift, and Routine Operations

| Signal / control | Source | Threshold / expected state | Response | Owner | Retention |
|---|---|---|---|---|---|
| Availability | Replace monitor. | Replace target or threshold. | Replace action. | Replace owner. | Replace retention. |
| Capacity / performance | Replace metric. | Replace warning and critical levels. | Replace response. | Replace owner. | Replace retention. |
| Configuration drift | Replace comparison source. | No unauthorized deviation. | Correct, except, or escalate. | Replace owner. | Replace retention. |

Document dashboards, logs, alerts, traces, synthetic tests, event correlation, false-positive handling, maintenance suppression, handoff, daily/weekly/monthly tasks, and review cadence.

## 20. Security, Identity, Credentials, Least Privilege, Audit, and Privacy Controls

- Identify approved authentication and authorization methods.
- Use roles or groups rather than undocumented direct assignments where required.
- Define credential, secret, key, token, certificate, and service-account ownership and rotation.
- Prohibit credentials, sensitive endpoints, protected information, or unnecessary internal details in Git.
- Define audit logging, privileged-action review, separation of duties, and periodic recertification.
- Identify privacy, data minimization, consent, disclosure, and breach-response requirements.
- State security stop conditions and required escalation paths.

## 21. Data Handling, Records, Retention, Evidence, and Chain of Custody

| Data / evidence class | Location | Access | Retention | Integrity / custody control |
|---|---|---|---|---|
| Operational evidence | Approved evidence source. | Need-to-know roles. | Approved schedule. | Immutable or attributable record as required. |
| Sensitive data | Approved protected location. | Authorized roles only. | Approved schedule. | Encryption and handling controls. |
| Temporary working data | Approved temporary location. | Assigned personnel. | Delete or sanitize after use. | Document disposition. |

Define correction, supersession, legal hold, export, audit access, evidence packaging, hashing, timestamps, time source, and chain-of-custody requirements when applicable.

## 22. Performance, Capacity, Availability, Reliability, and Service Levels

| Measure | Baseline | Target / threshold | Collection method | Owner | Action |
|---|---|---|---|---|---|
| Availability / SLO | Replace. | Replace. | Replace. | Replace. | Replace. |
| Capacity | Replace. | Warning / critical / forecast horizon. | Replace. | Replace. | Replace. |
| Performance | Replace latency, throughput, queue, or utilization measure. | Replace. | Replace. | Replace. | Replace. |
| Reliability | Replace failure, error, or recovery measure. | Replace. | Replace. | Replace. | Replace. |

## 23. Continuity, Backup, Restore, Disaster Recovery, RTO, and RPO

| Service / data set | Backup method | Frequency / retention | RPO | RTO | Recovery location | Test cadence |
|---|---|---|---|---|---|---|
| Replace | Replace. | Replace. | Replace. | Replace. | Replace. | Replace. |

Document failover authority, recovery sequence, dependency order, recovery communications, restoration validation, fallback, exercise schedule, lessons learned, and unresolved recovery gaps.

## 24. Communications, Notifications, Stakeholders, and Handoffs

| Event / phase | Audience | Message owner | Channel | Timing | Required content |
|---|---|---|---|---|---|
| Planned start | Replace. | Replace. | Replace. | Replace. | Scope, expected impact, support path. |
| Status / delay | Replace. | Replace. | Replace. | Replace. | Current state, risk, next update. |
| Completion / restoration | Replace. | Replace. | Replace. | Replace. | Result, validation, residual issues. |
| Escalation | Replace. | Replace. | Replace. | Replace. | Severity, impact, actions, decision needed. |

Include shift handoff, operations-center coordination, customer messaging, leadership updates, vendor coordination, and after-action distribution when required.

## 25. Training, Competency, Knowledge Transfer, Job Aids, and Exercises

| Audience / role | Required competency | Training method | Assessment | Refresher cadence | Evidence |
|---|---|---|---|---|---|
| Replace role | Replace knowledge, skill, and authorization. | Instructor-led, self-study, lab, simulation, or supervised execution. | Replace pass criterion. | Replace. | Training record. |

Include learning objectives, prerequisites, instructor notes, labs, simulations, exercises, scenario injects, evaluation, remediation, accessibility, and knowledge-transfer requirements.

## 26. Exceptions, Deviations, Waivers, Emergency Use, and Compensating Controls

| Field | Minimum content |
|---|---|
| Exception / waiver ID | Unique identifier linked to the authoritative record. |
| Exact scope | System, service, object, user, configuration, location, and duration. |
| Justification | Why the normal control cannot be met. |
| Risk | Exposure, likelihood, consequence, and affected mission. |
| Compensating control | Temporary control that limits risk. |
| Authority | Required owner, technical, security, privacy, records, and management approval. |
| Effective / expiration | No indefinite exception. |
| Restoration | Exact return-to-standard plan and validation. |

## 27. Troubleshooting, Known Errors, Decision Matrix, and Frequently Asked Questions

| Symptom / event | Probable cause | Diagnostic check | Corrective action | Escalation / record |
|---|---|---|---|---|
| Replace symptom. | Replace cause. | Replace safe diagnostic. | Replace bounded action. | Replace route. |

Add known errors, workarounds, unsupported actions, false positives, dependency failures, diagnostic decision trees, and escalation criteria. Do not place live credentials or sensitive endpoint inventories in this section.

## 28. Technician, Reviewer, and Closeout Checklists

| Phase | Checklist |
|---|---|
| Before | Qualified and assigned; controlling record; scope and owner verified; current source; access; dependency health; before state; backup; rollback; approvals; communications. |
| During | Follow numbered steps; capture evidence; protect credentials and sensitive data; observe hold and stop points; do not expand scope. |
| Validate | Functional, technical, security, data, performance, monitoring, recovery, and owner-acceptance checks completed as applicable. |
| Closeout | After state; result; exceptions; residual risk; reviewer; approvals; actual timing; evidence links; handoff; corrective actions; record closure. |

## 29. Metrics, Outcomes, Contribution Evidence, and Work Ledger Integration

- Define service, control, risk, quality, timeliness, reliability, customer, or mission outcomes.
- Distinguish output counts from meaningful outcomes.
- Record data source, formula, owner, cadence, threshold, and limitations.
- Use repository contribution evidence to show attributable document activity, not as a standalone measure of quality or performance.
- Map approved contributor identities to Work Ledger IDs and position numbers when integration is authorized.
- Prevent the document or repository from becoming an unauthorized personnel record.

## 30. Review, Recertification, Lifecycle, Supersession, Retirement, and Decommission

| Trigger / cadence | Review owner | Required review | Disposition |
|---|---|---|---|
| Material change | Document owner and affected technical owners. | Scope, authority, architecture, risk, procedure, tests, evidence. | Revise and approve. |
| Scheduled review | Named steward and approvers. | Currency, ownership, references, controls, exceptions, metrics. | Reapprove, revise, or retire. |
| Incident / audit / finding | Assigned owner. | Root cause, control gap, procedure effectiveness. | Corrective revision. |
| Retirement / replacement | Owner, records, security, and affected stakeholders. | Migration, record preservation, access removal, archive, redirects. | Supersede or retire. |

## 31. Appendices, Attachments, Diagrams, Forms, Samples, and Sanitized Examples

Use appendices for material that supports execution without interrupting the controlled procedure:

- Architecture and process diagrams
- RACI and contact-role matrices
- Checklists and forms
- Configuration schemas and data dictionaries
- Sanitized commands and expected outputs
- Test cases and acceptance forms
- Communication templates
- Risk and exception forms
- Evidence manifests and hashes
- Reference tables, catalogs, and mappings
- Training exercises and job aids

Store attachments under `docs/attachments/`. Do not include credentials, live secrets, transient tokenized URLs, protected data, or unnecessary internal inventory.

## 32. Release Gates, Concurrence, Approval, and Control Assurance

| Gate | Owner | Pass criterion | Evidence | Status |
|---|---|---|---|---|
| Content complete | Document steward | All required modules complete; unused optional modules removed. | Review checklist. | Open. |
| Technical review | Technical owner | Method, commands, architecture, validation, rollback, and monitoring are correct. | Review record. | Open. |
| Operational review | Operations owner | Procedure is executable, supportable, and integrated with work systems. | Review record. | Open. |
| Security / privacy / records review | Applicable control owners | Required controls and handling rules are satisfied. | Concurrence. | Open / N/A with authority. |
| Owner acceptance | Service / data / process owner | Outcome and residual risk are accepted. | Acceptance record. | Open. |
| Publication approval | Authorized approver | Version, status, effective date, review date, and revision entry are complete. | Release approval. | Open. |

<aside class="callout warning">
  <strong>Template release conclusion</strong>
  <p>A derived document must not be declared effective while placeholders remain, approvals are unresolved, repository intelligence is stale, required evidence is absent, or validation reports an error.</p>
</aside>
