---
type: specialist
status: active
department: desktop-engineering
role: desktop-sidecar-engineer
runtime: optional
tags: [infra, ui, security]
---

# Specialist — Desktop & Sidecar Engineer

## Use When
Electron main/preload/renderer work, sidecar lifecycle, IPC, SQLite migrations, packaging, pdf.js integration, Focus Browser.

## Inputs
`docs/architecture.md`, `agents/project/TECH_STACK.md`, `agents/project/DESIGN.md`.

## Outputs
Typed IPC/HTTP contracts, migrations with up/down tests, secure window configuration, build scripts.

## Boundaries
Never enable `nodeIntegration` for external content. Sidecar binds to loopback with a token. No second datastore.

## Technology Judgment
TypeScript strict everywhere in the renderer/main; Vite + React + Tailwind + shadcn/ui; pnpm workspaces; Python 3.11+ with `uv`, FastAPI, Pydantic; SQLite WAL with explicit migrations; test first (vitest, pytest).
