---
type: department
status: active
tags: [infra, security, ui]
---

# Department — Desktop Engineering

Owns Electron shell, Python sidecar, SQLite, packaging, security boundaries, privacy/legal review of integrations.

## Specialists
- [[specialists/desktop-sidecar-engineer]]
- [[specialists/privacy-legal-reviewer]]

## Coverage Matrix
| Category | Covered by | Status |
|---|---|---|
| Domain expertise | — | n/a |
| Product/strategy | — | n/a |
| Architecture/engineering | desktop-sidecar-engineer | covered |
| Design/UX/content | `agents/project/DESIGN.md` (no dedicated designer) | partial |
| Data/AI | — (see ai-platform) | n/a |
| Security/compliance | privacy-legal-reviewer | covered (advisory, not legal advice) |
| QA/testing | CI + `pnpm verify` | covered |
| Operations/support | — | not needed |
| Platform/tooling/integration | Electron, uv, pnpm, OpenPets, Telethon | covered |

**Coverage gap:** no dedicated UI/visual designer; DESIGN.md is a starting contract. Revisit at Phase 3 gate (pet/popups are the most design-sensitive).
