---
type: research
status: active
tags: [research, pet, focus-guard, windows, external]
informs: ["[[roadmap/PHASE_3]]"]
---

# OpenPets and Focus Guard spike (WU-P03-003, WU-P03-005) — Windows result

Date: 2026-11-02 · Machine: **owner laptop** (Windows 11, Node 22.16.0). Everything below was run there. Nothing was installed into the repo; spike scripts lived in the session scratch folder.
Status: WU-P03-003 **blocked** (two owner/manual items open), WU-P03-005 **spike decided: `active-win`** (implementation not started).

## What was installed (and how it was verified)
| Item | Evidence |
|---|---|
| `OpenPets-4.1.0-win-x64-setup.exe`, 216,452,280 bytes, from GitHub release v4.1.0 | SHA-256 `4b6424b6fc0a14412f88d79907e4437bfda816db7b8e282b0e90b654f065f8be` equals the digest GitHub publishes for the asset; Authenticode status `Valid`, signer `SignPath Foundation` |
| Installed with `/S` (silent), exit 0, per-user at `C:\Users\HP\AppData\Local\Programs\openpets` (653 MB on disk) | uninstall entry "OpenPets 4.1.0"; `openpets.exe` runs, window "OpenPets Default Pet" |
| No autostart registered by OpenPets | `HKCU\...\Run` has no entry matching `openpets` |
| `@open-pets/client` 4.1.0, MIT | `npm view` license; installed with `--ignore-scripts`, 0 vulnerabilities |
| Repo licence MIT | GitHub API `license.spdx_id` |

## OpenPets over named-pipe IPC (real run)
`createOpenPetsClient()` finds the endpoint through the discovery file (`%APPDATA%\OpenPets\runtime\ipc.json`, holds endpoint + token; the token was never printed). The app listens on a named pipe `openpets-<hash>-<pid>`.

| Call | Result | Latency |
|---|---|---|
| `hello()` | `{ok, protocol: openpets-ipc, protocolVersion: 1, appVersion: 4.1.0}` | 9 ms |
| `status()` | app running, default pet `builtin` "Hoodie Cat", speech bubbles enabled | 3 ms |
| `listPets()` | one pet (the built-in) | 4 ms |
| `react("working")` | `{ok:true, shown:true}` | 14 ms |
| `say("Session shuru. Focus!")` | `{ok:true, shown:true}` | 17 ms |
| `say` with 2000 chars | rejected, `invalid_params: Message is too long.` | 6 ms |

Limits found by bisection: **`say` max 140 characters**; Hindi (Devanagari) text is accepted. Valid reactions (`allowedReactions`): `idle, thinking, working, editing, running, testing, waiting, waving, success, error, celebrating`. `celebrate` and `sleepy` are rejected with `invalid_reaction`. IPC messages are line-delimited JSON, 16 KB max (docs/ipc.md).

`shown:true` means the app accepted the command. **Whether the bubble was visible on screen was not checked by me** (no screenshot). The owner confirmed in chat on 2026-11-02 that it was visible.

## Official plugins (state file `%APPDATA%\@open-pets\desktop\openpets-plugin-state.json`)
Enabled out of the box (bundled): Quick Reminders, Simple Timer, **Anxiety Aid Tools**, **Focus Buddy**, Launch Buddy, Daily Fortune Cookie. Bundled but disabled: Virtual Pet, System Resources.
**Not installed: Mood Check-in and Water Reminder.** They are in the plugin catalog and are installed from the app's Control Center (UI), which was not driven in this run.

## Pet licence
Bundled pet is "Hoodie Cat" (id `builtin`). The repo has a top-level MIT `LICENSE`. **A separate licence for the Hoodie Cat spritesheet was not found or read, so the pet-art licence is UNVERIFIED** (assumed covered by the repo licence). Third-party pets must have their licence checked before install.

## ActivityWatch (Tauri build) did not work here
`activitywatch-tauri-v0.14.1-windows-x86_64-setup.exe` (43,559,218 bytes; SHA-256 `19a0a6ffc6ea5db66dd63cc201b58b62843b1e21e157b4fe20774594a4c74de1` equals the GitHub digest; **NotSigned**). Installed (`D:\Users\HP\AppData\Local\Programs\ActivityWatch-Tauri`), exit 0.
- `aw-tauri.exe` starts, but only that one process runs: no `aw-server`, no watchers, nothing listens on `:5600`.
- `aw-tauri.log` repeats `Unable to start transaction! ... database is locked` every ~6 s, starting right after "Fresh database".
- Reproduced a second time after deleting the new empty `sqlite.db`, `-shm`, `-wal` (0 buckets, no user data): same error.
- Cause **unknown** (not profiled). The classic 81.5 MB build (`activitywatch-v0.14.1-windows-x86_64-setup.exe`) was **not tried**.
- Side effect undone: the app had written an autostart entry (`HKCU\...\Run\aw-tauri`); I removed it and stopped the process. The program itself is still installed.

## Focus Guard: `active-win` works
`active-win` 9.0.0, MIT (`npm view`), sindresorhus. It needs its install script (`node-pre-gyp`), which downloads a prebuilt N-API binary from the project's own GitHub release; with `--ignore-scripts` it returns `undefined` (my first run did that, not a package fault). After `npm rebuild active-win`: first call **306 ms**, then **2 ms**, returns `title`, `owner.name`, `owner.path`, `url` (null here; browser URL support on Windows is **unverified**).
Finding for the design: the foreground window it returned was **the pet's own window** ("OpenPets Default Pet"), so Focus Guard must ignore OpenPets and JARVIS windows.
`npm audit` reports a moderate `minimatch` DoS advisory (GHSA-g3hv-75wg-m249) in the install-time dependency tree (`cacache`, `glob`); not a runtime path, but record it in the BOM.
Browser tab titles/URLs are not covered; a browser extension (`aw-watcher-web`) would be needed and is out of scope here.

## Decisions for the owner / next steps
1. WU-P03-005 uses **`active-win`** (works, MIT, tiny). ActivityWatch stays off the plan unless the classic build is tried and works.
2. Open for WU-P03-003: owner confirms the "Session shuru. Focus!" bubble and the "working" animation were visible; Mood Check-in and Water Reminder get installed from the Control Center; Hoodie Cat art licence gets checked.
3. API stability: client protocol is `v1`, package is at 4.1.0 and very active (last push 2026-10-30); pin `@open-pets/client` exactly and wrap it behind our own `PetClient` so a protocol bump touches one file.
