# Design

> Design contract for implementation. Strategy and rationale: `docs/04-UX-STRATEGY.md`. Values below are a starting point; verify WCAG AA contrast when implementing WU-P01-002 and adjust.

## Visual Theme & Atmosphere
"Study dojo": calm, focused, quietly motivating. Dark-first (long reading sessions), with a warm paper-like light mode. Gamification is subtle and adult: progress rings, XP, a small companion. No cartoonish confetti. Density: comfortable, reading-friendly. Known references: Obsidian (calm notes), Linear (clarity), Anki (function over form) — taken as mood only, nothing copied.

## Color Palette & Roles
| Role | Dark | Light | Use |
|---|---|---|---|
| `bg` | `#0F1220` | `#FAF7F2` | App background |
| `surface` | `#171B2E` | `#FFFFFF` | Cards, panels |
| `surface-2` | `#1F2440` | `#F1ECE3` | Raised/hover |
| `text` | `#E8EAF2` | `#1B1E2B` | Primary text |
| `text-muted` | `#9AA1BD` | `#5B6178` | Secondary text |
| `accent` (saffron) | `#F4A340` | `#C97A12` | Primary action, XP |
| `accent-fg` (text on accent) | `#0F1220` | `#1B1E2B` | Button text; light-theme white failed AA (3.35:1), dark text measured 4.5:1+ in tokens.test.ts |
| `info` (indigo) | `#6C7CFF` | `#4553D6` | Links, focus ring |
| `success` / Green tag | `#3FB68B` | `#1F8A64` | Pass, confident ✓ |
| `warning` / Amber tag | `#E5B13A` | `#A87A0E` | 50-50, caution ◐ |
| `danger` / Red tag | `#E5645B` | `#C23A31` | Fail, guess ✕ |
Unknowns: final brand name/logo (none yet). Confidence tags always pair color with an icon.

## Typography Rules
- UI: Inter. Hindi: Noto Sans Devanagari (must render cleanly everywhere). Long-form notes/answers: Source Serif 4.
- Scale (px): 12 / 14 / 16 (body) / 20 / 24 / 32. Line-height 1.5 for body, 1.3 for headings.
- Reader text is user-resizable; never below 14px in app chrome.

## Component Styling
- Base: shadcn/ui + Tailwind, tokens above as CSS variables.
- Buttons: one primary (accent fill) per screen; secondary = outline; destructive = danger outline.
- Cards: `surface`, 12px radius, 1px subtle border, no heavy shadows in dark mode.
- Progress: rings for daily/weekly, bars for syllabus nodes; label always shows `% verified`.
- Quiz option: large hit area, keyboard 1–4, confidence tag row (G/A/R) beneath.
- Inputs: visible focus ring (`info`), error text with icon.
- States: every list/table has empty, loading, error states (friendly, one next action).

## Layout Principles
- 4px spacing grid; sidebar (collapsible) + main + optional right panel (AI/notes).
- One primary action per screen ("Next block").
- Reader screen: reading area dominates; controls fade during focus.
- Gate screen: full-window, no navigation (focus).

## Responsive Behavior
- Desktop only. Minimum window 1100×700. Sidebar collapses under 1200px. Split-view needs ≥ 1300px (else tabbed).
- Touch targets ≥ 40px (for touchscreen laptops).

## Do's and Don'ts
- Do show source (book + page) next to any AI-derived fact.
- Do keep pet language supportive (see `docs/04-UX-STRATEGY.md` §9).
- Do honour `prefers-reduced-motion`.
- Don't use color as the only signal.
- Don't show "predicted marks"; use "practice score (range)".
- Don't add streak-loss alarms or public rankings.
- Don't render AI output as HTML without sanitizing.

## Agent Prompt Guide
- "Use tokens from `agents/project/DESIGN.md`; dark theme default; shadcn components; no new colors."
- "Every new screen: empty/loading/error states and keyboard access."
- "Any number shown as progress must state what it measures (e.g., '62% verified')."
