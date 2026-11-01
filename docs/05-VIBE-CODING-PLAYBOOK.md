# Vibe-Coding Playbook (Hinglish)

> Aap **Director** ho. AI coding agent **Builder** hai. Aapka kaam: chhote, clear kaam dena, har kaam ke baad check karna. "Poora app bana do" kabhi mat bolna.

## 0. 5 Golden Rules
1. **Ek Work Unit (WU) = ek commit.** Chhota rakho. Ek WU ka goal ek hi hona chahiye.
2. **Spec pehle, code baad mein.** `specs/*.feature` mein behavior likha hai. Agent pehle test likhega.
3. **Agent ko rules do, yaad mat rakho.** `CLAUDE.md` / `AGENTS.md` mein rules hain. Kisi bhi agent ko pehle ye file padhne ko bolo.
4. **Verify bina "done" nahi.** `pnpm verify` green ho + aap 2 minute app mein khud dekho.
5. **Atak jao to revert karo, aur zyada mat jodo.** `git revert` ya WU dobara.

## 1. Ek baar ka setup (ye cheezein sirf aap kar sakte ho)

| # | Kaam | Kyun |
|---|---|---|
| 1 | **Node.js 20+** aur **pnpm** install | Electron/React |
| 2 | **Python 3.11+** aur **uv** install | Sidecar |
| 3 | **Git** | Version control |
| 4 | **Ollama** install, phir ek chhota model pull karo (3–4B parameters ke aas-paas, Ollama library mein jo current recommended ho) | Offline fallback |
| 5 | `npm install -g omniroute` phir `omniroute` chalao, dashboard (`localhost:20128`) mein **sirf free providers** connect karo, **billing kisi par enable mat karna** | Free AI gateway |
| 6 | **Google AI Studio** se free API key lo | Mains vision (T3) |
| 7 | Ek coding agent chuno: **Claude Code**, **Antigravity (Gemini Pro)**, ya **OpenCode** | App banane ke liye |
| 8 | Is repo ko clone karo aur agent mein khol do | |

> **Phase 7 mein** (Telegram): `my.telegram.org` se `api_id` / `api_hash` aap khud lenge. Ye mere paas nahi ho sakta.
> **Phase 2/3/4 mein**: syllabus tree, PYQ tagging, aur quotes ka **human review** aap karoge. Isse skip mat karna, ye quality ka base hai.

## 1b. Windows-specific (aapka laptop)

| Cheez | Kya karo |
|---|---|
| **Git for Windows** install karo | WUR hooks `sh` se chalte hain; Git for Windows ka bundled `sh` PowerShell/cmd/Git Bash sab se kaam karta hai |
| **Line endings** | Repo mein `.gitattributes` hai jo hooks/scripts ko **LF** par rakhta hai. CRLF hone par hooks silently toot jaate hain. Agar hook error aaye: `git config --global core.autocrlf input` set karke repo ko **dobara clone** karo (sabse safe tareeka; local changes pehle push/backup kar lo) |
| **Python** | **3.11 ya 3.12** (3.14 avoid; laya ka purana Windows crash fix ho chuka hai par naye versions par risk kyun) |
| **uv** | PowerShell mein uv ka official installer chalao, phir `uv sync` |
| **Node** | 20+ aur `pnpm` (`corepack enable`) |
| **Ollama** | Windows installer; phir ek chhota model pull |
| **OmniRoute** | PowerShell: `npm install -g omniroute`, phir `omniroute` |
| **OpenPets** | Releases page se `OpenPets-*-win-x64-setup.exe` (signed) |
| **Paths** | Scripts mein hardcoded `/` ya `C:\...` nahi; agent ko bolo `pathlib`/`path.join` |
| **Long paths** | Agar `node_modules` ya PYQ file names par error aaye: Windows long paths enable karo (admin) |
| **Antivirus** | Defender dev folders ko slow kar sakta hai; exclusion aap apne risk par |

## 2. Roz ka loop (har WU ke liye)

```
1. Phase file kholo:           agents/roadmap/PHASE_N.md
2. Agla "planned" WU chuno
3. Agent ko ye prompt do:      (neeche template)
4. Agent test likhta hai → code → test pass
5. Aap:                        pnpm verify   +   app mein 2-min manual check
6. Commit message:             WU-P02-006: add start/end bookmark
7. Roadmap table mein WU ko    ready-for-review karo, phir aap "accepted" karo
```

Agar aap **Claude Code + WUR plugin** use karte ho: `/wur:start 1` phase contract banata hai. Git hooks (`.githooks/`) galat commit message ko block kar denge.

### Universal prompt template (copy → paste)

```
Repo rules: pehle CLAUDE.md aur docs/architecture.md padho.
Phase file: agents/roadmap/PHASE_{N}.md → kaam: WU-P{NN}-{NNN}.
Sirf isi WU ka scope karo. Koi extra feature nahi.
Pehle specs/ ke relevant scenarios ko failing test mein badlo (red),
phir minimal code (green), phir refactor.
Naye dependency se pehle: npm view / pip index + LICENSE check, aur BOM (docs/02-REPO-BOM.md) mein entry.
Khatam hone par: pnpm verify chalao aur output dikhao. Commit mat karo; mujhe diff dikhao.
```

## 3. Kaun sa agent kis kaam ke liye

| Kaam | Suggestion |
|---|---|
| Boilerplate (scaffold, UI screens, CRUD) | Antigravity / OpenCode (Gemini, free-ish quota) |
| Tricky logic (FSRS integration, bookmark offsets, evaluator prompts) | Jo sabse strong model aapke paas ho |
| Review | Dusre agent se diff review karao ("is diff mein bugs/security issues dhoondo") |

Sab agents ko same `CLAUDE.md`/`AGENTS.md` rules milte hain.

## 4. Phase 1 ke prompts (reference)

**WU-P01-001: Repo scaffold**
```
pnpm workspace banao: apps/desktop (Electron+Vite+React+TS), apps/sidecar (Python, uv), packages/shared.
ESLint, Prettier, tsconfig strict, ruff, pytest, vitest. Root par `pnpm verify` = lint + typecheck + tests (dono sides).
README mein 5 line ka "kaise chalayein". Koi feature nahi.
```

**WU-P01-002: Electron shell**
```
Electron + React Router: screens (Today, Study, Syllabus, PYQ, Mains, CA, Interview, Browser, Insights, Settings) sab empty placeholder.
Tailwind + shadcn/ui. Theme tokens agents/project/DESIGN.md se (dark default). contextIsolation true, sandbox true, nodeIntegration false.
```

**WU-P01-003: Sidecar**
```
FastAPI: GET /health. Electron main isse spawn kare random port par, per-launch bearer token ke saath, 127.0.0.1 only.
App band hone par sidecar bhi band ho. OpenAPI se typed TS client generate karo. Test: sidecar bina token ke 401 de.
```

**WU-P01-004: SQLite**
```
SQLite (WAL) schema v1 + migrations: syllabus_node, link, document, chunk (+FTS5), study_session, question, attempt, card, review_log,
llm_cache, llm_usage, setting. sqlite-vec verify karo. Test: migrate up/down, FTS5 query, recursive CTE on syllabus_node.
```

**WU-P01-005: LLMClient**
```
apps/sidecar/jarvis/llm/: LLMClient.complete(task, messages, schema?) → tier table (config/routing.yaml) se provider chune:
OmniRoute (OpenAI-compatible, localhost:20128), Ollama, Gemini direct. Cache by sha256, llm_usage ledger, fallback ladder.
Settings screen par "Test AI" button. Tests fake providers ke saath: fallback, cache hit, schema retry.
```

## 5. Jab atak jao

| Problem | Karo |
|---|---|
| Build fail | Error agent ko do: "Is error ka root cause batao, phir minimal fix. Naya feature nahi." |
| Agent ne bahut kuch badal diya | `git diff --stat` dekho. Scope se bahar ho to `git checkout -- <files>` aur WU chhota karo |
| LLM output kharab | Golden test mein case add karo, prompt version badhao, cache invalidate |
| Free quota khatam | Quota ledger dekho, Ollama fallback, ya Web Assist (T4) |
| Kuch samajh nahi aa raha | Agent se bolo: "10 line mein explain karo ye module kya karta hai aur kya nahi" |
| Sidecar (OmniRoute) toota | Version pin check karo; Plan B: LiteLLM adapter (ek file) |

## 6. "Done" ki definition (har WU)
- [ ] Acceptance criteria (phase file) poore
- [ ] Naya test pehle fail hua, phir pass hua
- [ ] `pnpm verify` green (fresh output)
- [ ] Koi naya secret/key repo mein nahi
- [ ] BOM aur architecture ke rules follow hue
- [ ] Commit message `WU-Pnn-nnn: ...`
- [ ] Phase file mein status `ready-for-review`; aap `accepted` karte ho

## 7. Aap kitna manual kaam karoge (honest list)
- Setup (section 1): ek baar.
- **Review**: ontology (P2), PYQ tags (P4), quotes (P3), 50 MCQ grading (P2).
- **Dogfood**: roz padhai app mein, phir feedback.
- Baaki sab agent karega, aapko sirf prompt + check.
