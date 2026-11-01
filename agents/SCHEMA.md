---
schema_version: 1
---

# agents/ Wiki Schema

> Schema version: **1** (the `wiki` layout). When the WUR plugin ships a newer
> schema, run `/wur:upgrade` to migrate. Never hand-edit `schema_version`.

## Page Types
| Type | Location | Description |
|---|---|---|
| `phase` | `agents/roadmap/PHASE_*.md` | One execution phase |
| `fix-round` | `agents/roadmap/PHASE_*_FIX.md` | Legacy fix ledger; readable for old work, not created for new work |
| `fix-round` | `agents/roadmap/FIX_*.md` | Legacy bug fix batch file; readable for old work only |
| `research` | `agents/research/*.md` | Ingested external source or analysis |
| `decision` | `agents/docs/*.md` | Architectural decision record |
| `note` | `agents/docs/*.md` | Durable note, synthesis, or concept page |
| `report` | `agents/reports/*.md` | Durable report or summary |
| `department` | `agents/departments/*.md` | Project-specific capability area |
| `specialist` | `agents/specialists/**/*.md` | Project-specific expert role card |

## Status Values
`planned` · `active` · `done` · `blocked` · `deferred` · `aborted`

## Work Unit Status Lifecycle
`planned -> active -> ready-for-review -> accepted -> done`

Agents may set `planned`, `active`, `ready-for-review`, `blocked`, and `deferred`.
Only the client may set `accepted` or `done`.

## Contract Boundary
- `agents/` is the source-of-truth wiki.
- `contracts/rule.md` stores shared execution rules outside `agents/`.
- `contracts/PHASE_{n}_CONTRACT.md` stores phase task brief, Allowed Read References, and executor report ledger.
- Executor handoff reports stay in the active phase contract.
- `agents/reports/` stores durable WUR reports and summaries, not executor handoff ledgers.
- If a worktree is used, exclude `agents/` and `contracts/`; keep WUR state in the main project root only.

## Graph Scope
Graph pages (must have frontmatter):
- `agents/roadmap/PHASE_*.md`
- `agents/roadmap/PHASE_*_FIX.md`
- `agents/roadmap/FIX_*.md` (legacy)
- `agents/research/*.md`
- `agents/docs/*.md`
- `agents/reports/*.md`
- `agents/departments/*.md`
- `agents/specialists/**/*.md`

System pages (may omit frontmatter):
- `agents/project/PHILOSOPHY.md`
- `agents/project/USAGE.md`
- `agents/project/DESIGN.md`
- `agents/project/TECH_STACK.md`
- `agents/roadmap/ALL.md`
- `agents/roadmap/log.md`
- `agents/SCHEMA.md`
- `agents/index.md`
- `agents/references/*`
- `agents/raw/*`

## Required Frontmatter (graph pages)
- `type` — one of the page types above
- `status` — one of the status values above
- `tags` — YAML list of lowercase kebab-case strings, even if empty (`tags: []`)

## Specialist Registry
`agents/departments/` and `agents/specialists/` describe project-specific expertise. They are advisory unless explicitly assigned a WU. Runtime subagents are optional; if unavailable, the coordinator applies the role locally. Coordinator owns final planning and execution decisions. Specialist output must be consolidated: one recommendation is not one Work Unit.

Department pages must include `## Coverage Matrix`. Coverage categories are checklists, not mandatory files. Start from domain expertise, product/strategy, architecture/engineering, design/UX/content, data/AI, security/compliance, QA/testing, operations/support, and platform/tooling/integration. Domain examples are illustrative, not exhaustive. For game projects, check game design, level design, gameplay/engine, art/technical art, audio, QA/playtest, production, and platform-specific expertise. Record any missing critical capability as a `coverage gap`.

Specialist frontmatter:
```yaml
type: specialist
status: active
department: engineering
role: frontend-architect
runtime: optional
tags: [ui]
```

Specialist body must include:
- `## Use When`
- `## Inputs`
- `## Outputs`
- `## Boundaries`
- `## Technology Judgment` for implementation-facing roles

Technology Judgment defaults are recommendations, not mandates. Prefer TypeScript for non-trivial web/app code, consider Vite + React first for common frontend web apps, consider Tailwind CSS + shadcn/ui for common React web UI, consider Bun when compatible, and avoid plain HTML/CSS/JS for app-scale work unless explicitly requested or clearly tiny/static. Create or update `agents/project/TECH_STACK.md` before execution when stack choices matter.

## Graph Conventions
- `depends_on: ["[[roadmap/PHASE_1]]"]` — phase dependency
- `parent: "[[roadmap/PHASE_1]]"` — legacy fix-round or related page belongs to a phase
- `verifies: ["[[roadmap/PHASE_1]]"]` — report verifies a phase or legacy fix round
- `informs: ["[[roadmap/PHASE_1]]"]` — research or docs inform another graph page
- Use path-style wikilinks like `[[roadmap/PHASE_1]]`, not `[[PHASE_1]]`
- Every `[[wikilink]]` creates an edge in Obsidian graph view

## Tag Conventions

`tags:` is a YAML list of lowercase kebab-case strings. Always a list, even when empty (`tags: []`). Never a string.

### Format rule
```yaml
tags: [auth, breaking-change, spike]   # correct
tags: [Auth, Breaking Change]            # wrong — uppercase, spaces
tags: auth                              # wrong — must be a list
```

### Predefined vocabulary

Use these names before inventing new ones. Consistent names make graph filtering useful.

**Scope** — what area of the system this touches:
| Tag | Meaning |
|---|---|
| `api` | External API contract or boundary |
| `auth` | Authentication or authorization |
| `data` | Data model, schema, or migration |
| `infra` | Infrastructure, environment, or deployment |
| `ui` | User interface |
| `security` | Security-sensitive change |
| `performance` | Performance impact |

**Risk** — signal extra caution:
| Tag | Meaning |
|---|---|
| `breaking-change` | Introduces a breaking change |
| `migration` | Data or structural migration |
| `risky` | High-risk, needs extra review |

**Process** — how the work was done:
| Tag | Meaning |
|---|---|
| `spike` | Exploratory phase — waived tests acceptable |
| `research` | Knowledge-gathering, no production code |

**Source** — for `research/` pages only:
| Tag | Meaning |
|---|---|
| `external` | Ingested from external URL or file |
| `archived` | Source is no longer maintained |

**Operational visibility tags** — temporary observation signals for Obsidian and graph filtering. Tags are observation signals; status fields remain authoritative.
| Tag | Meaning |
|---|---|
| `state-planned` | Page represents planned work or knowledge |
| `state-active` | Page is currently in active attention |
| `state-ready-review` | Work is ready for client or human review |
| `state-accepted` | Client accepted the WU or decision |
| `state-done` | Page represents completed work or resolved knowledge |
| `state-blocked` | Work is blocked |
| `state-deferred` | Work is intentionally deferred |
| `state-aborted` | Work was abandoned |
| `needs-review` | Needs human or specialist review |
| `needs-client` | Needs client decision or confirmation |
| `open-question` | Contains an unresolved question |
| `contradiction` | Contains or tracks a contradiction |
| `decision-conflict` | Competing decisions must be resolved |
| `coverage-gap` | Critical specialist/domain coverage is missing |
| `test-failing` | Verification is failing |
| `test-waived` | Verification was waived with a recorded reason |
| `graph-stale` | Derived graph artifacts need refresh |
| `risk` | Needs extra risk attention |
| `phase` | Phase page |
| `work-unit` | Work Unit content or WU-specific page |
| `fix-round` | Legacy fix ledger or fix-round content |
| `decision` | Decision content |
| `report` | Durable report or summary |
| `specialist` | Specialist role content |
| `design` | Design contract or design-related content |
| `tech-stack` | Technology stack content |

Remove attention tags such as `needs-review`, `open-question`, `contradiction`, `coverage-gap`, `test-failing`, and `graph-stale` when the issue is resolved. Keep the authoritative state in `status`, `test_status`, phase tables, and roadmap files.

Custom project-specific tags are allowed. They must be lowercase kebab-case and documented in this file under a `## Project Tags` section.

### Lint rules (checked by `/wur:wiki:lint`)
- Every tag must match `^[a-z][a-z0-9-]*$`
- `tags:` must be a list, not a scalar
- Unknown tags (not in predefined vocabulary and not in `## Project Tags`) are flagged as warnings, not errors

Run `/wur:wiki:upgrade` to add `agents/graph/ontology.yaml`, `agents/graph/README.md`, and the full graph layer.

## Project Tags
| Tag | Meaning |
|---|---|
| `study-loop` | Core loop: bookmark, timer, gate, FSRS, coverage |
| `llm` | LLM routing, prompts, evaluation harness |
| `content-review` | Needs owner review of learning content (ontology, PYQ tags, quotes) |
| `legal` | Licence, ToS or copyright consideration |
| `habit` | Gamification / habit-formation / wellbeing |
