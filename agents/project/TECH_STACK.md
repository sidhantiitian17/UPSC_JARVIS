# Tech Stack

## Selected Stack
- Project type: desktop (local-first) + AI orchestration
- Frontend/UI: Electron + Vite + React + TypeScript + Tailwind CSS + shadcn/ui + React Router; pdf.js for reading; MediaPipe Tasks (JS) for interview vision (Phase 9)
- Backend/API: Python 3.11+ FastAPI sidecar (one process), managed with `uv`
- Database/storage: SQLite (WAL) + FTS5 + sqlite-vec; library folder (PDFs) and Obsidian vault folder (markdown) chosen by the user
- Runtime/package manager: Node 20+ with pnpm; Python with uv
- AI: `LLMClient` → OmniRoute (sidecar, `localhost:20128`) | Ollama (`localhost:11434`) | Gemini API (free key)
- Decision Brain: `DecisionClient` → rules | fastembed+LR baseline | laya (adopted per head after the Phase 0 bake-off); see `docs/06-BRAIN-DECISION-MODEL.md`
- Companion: OpenPets (external app) via `@open-pets/client` local IPC (Windows named pipe)
- Hardware: 16 GB RAM, Ryzen 5 5600H (integrated Radeon; discrete GPU unconfirmed) → CPU-first inference
- Platform: Windows 10/11, Python 3.11/3.12, Git for Windows; data tooling in `tools/pyq`, `tools/brain`

## Decision
- Why this stack fits: single developer using AI agents; desktop + embedded browser + webcam needs Chromium; all ML-ish libraries (FSRS, OCR, Whisper, Telethon) are best in Python; SQLite keeps everything one file and free. See `docs/architecture.md` ADR-001…014.
- Overrides from defaults: WUR default suggestions target web apps; this is a desktop app, so Electron replaces Next.js/Vite-web. Python replaces Node backend for ML library fit. SQLite replaces Postgres/Supabase (single user, offline).
- Verification commands (to exist after WU-P01-001/007): `pnpm verify`; `cd apps/sidecar && uv run pytest && uv run ruff check .`

## Default Stack Suggestions
| Project type | Suggested default | Backend / data default |
|---|---|---|
| SPA / dashboard / CRM | Vite + React + TypeScript + Tailwind CSS + shadcn/ui + React Router | Supabase, or Node/Bun + PostgreSQL |
| SEO / marketing / blog | Next.js App Router + TypeScript + Tailwind CSS + shadcn/ui | Next.js API routes + Prisma + PostgreSQL when needed |
| Static site / docs | Astro + TypeScript + Tailwind CSS, plus Starlight for docs-heavy sites | None by default |
| Lightweight web app | Vite + Svelte/SvelteKit + TypeScript + Tailwind CSS + shadcn-svelte | SvelteKit backend or PocketBase |
| Fullstack type-safe | Next.js App Router + TypeScript + tRPC + Tailwind CSS + shadcn/ui + Prisma | PostgreSQL |
| Realtime app | Vite/Next.js + React + TypeScript + Tailwind CSS + shadcn/ui + WebSocket/Socket.io | Node/Bun + Redis + PostgreSQL |
| Mobile app | Expo + TypeScript + NativeWind + Tamagui or React Native Paper | Supabase or Firebase |
| AI app | Next.js or Vite + React + TypeScript + Tailwind CSS + shadcn/ui + OpenAI/Vercel AI SDK | Next.js API routes; LangChain only when useful |
| Web game 2D | Vite + TypeScript + Phaser | Optional Node/Bun service |
| Web game 3D | Vite + TypeScript + Three.js or React Three Fiber | Optional Node/Bun service |

## Not chosen (see `docs/architecture.md` → Don't Use Now)
PostgreSQL/AGE, new-api, LightRAG (deferred), Tauri, sioyek, Pathway, Rust webctl, Redis/Kafka/Kubernetes.
