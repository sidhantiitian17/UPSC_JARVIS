# UX Strategy (Hinglish)

> Framework: Teresa Torres (Opportunity Solution Tree), JTBD (Kalbach/Moesta), Google HEART, Papanek-style ethics check. Ye document batata hai **kya banana hai aur kyun**, UI ka *look* `agents/project/DESIGN.md` mein hai.

## 1. Strategy brief

| | |
|---|---|
| **User** | Ek UPSC aspirant (aap), jo roz limited ghante padhta hai aur "vibe coding" karta hai. |
| **Desired outcome (product)** | Roz ke focused minutes ka **zyada se zyada hissa yaad rahe**, aur student ko pata ho ki syllabus mein kahan khada hai. |
| **North Star** | **Verified Retained Minutes / week** = wo focused minutes jinke baad ka recall test ≥ 70% pass hua. |
| **Business viability** | N/A (personal tool, ₹0). Viability = *builder burnout se bachna*: scope chhota. |
| **Competitive position** | Coaching apps *content* bechte hain. Ye app *aapki padhai ka process* control karta hai. Direct competitor nahi. Blue-ocean slice: **"padha hua verify karne wala study OS"**. |

## 2. Main Job (JTBD)

> **Jab** mere paas roz sirf kuch ghante hain aur resources bahut saare hain,
> **main chahta hun** ki mera time sahi cheez par, sahi tareeke se lage aur *yaad rahe*,
> **taaki** main bina guilt ke, confidence ke saath exam ke liye ready ho sakun.

| Job type | Statement |
|---|---|
| Functional | Syllabus cover karna, revise karna, practice se evaluate karna |
| Emotional | "Mai sahi direction mein hun" ka bharosa, guilt kam, momentum |
| Social | Apni nazar mein "serious aspirant" |

### Job map (8 stages) aur underserved needs

| Stage | Desired outcome (minimize…) | Importance | Satisfaction (aaj) | Opportunity |
|---|---|---|---|---|
| Define | time to decide "aaj kya padhna hai" | High | Low | 🔥 |
| Locate | time to find "wo paragraph" jo PYQ mein aaya | High | Low | 🔥 |
| Prepare | setup friction (PDF kholo, timer, notes) | Med | Med | — |
| Confirm | uncertainty "mujhe ye aata hai?" | High | **Very low** | 🔥🔥 |
| Execute | distractions during reading | High | Low | 🔥 |
| Monitor | % padha hua jo bhool gaya | High | **Very low** | 🔥🔥 |
| Modify | time to fix weak topics | High | Low | 🔥 |
| Conclude | confusion "kitna bacha hai" | High | Low | 🔥 |

(Scores mere assumptions hain, user-research data nahi. 2–3 aspirants ke saath 20-min interviews se validate karna.)

## 3. Opportunity Solution Tree

```
OUTCOME: Verified Retained Minutes ↑
├─ O1  "Padhta hun par yaad nahi rehta"            → Recall Gate (P2) · FSRS (P2) · Weekly consolidation (P3)
├─ O2  "Pata nahi kya cover hua, kya baaki"        → Syllabus tree + honest coverage (P2) · Forecast (P3)
├─ O3  "Phone/YouTube/Telegram mein kho jata hun"  → Focus Guard (P3) · Pet (P3) · Focus Browser (P8)
├─ O4  "Prelims mein traps mein fas jata hun"      → PYQ Lab + Trap stats + Mistake Autopsy (P4)
├─ O5  "Mains answer ka feedback nahi milta"       → Mains Studio + Rubric (P5)
├─ O6  "Current affairs ka overload"               → CA digest + CA↔static links (P6)
├─ O7  "Interview ka darr, practice kahan?"        → Interview Room (P9)
└─ O8  "Resources bahut, revision kam"             → Source Budget alert (P2) · Revision cycles (P3)
```

**Pehle kaun si opportunity?** O1 + O2 (sabse underserved, sabse kam cost, baaki sab inke upar bante hain). Isliye Phase 2 = Study Loop.

## 4. Riskiest assumptions (leap-of-faith)

| # | Assumption | Type | Test (chhota) | Success criterion (pehle se tay) |
|---|---|---|---|---|
| A1 | LLM-generated MCQs itne accurate honge ki student pe bharosa kare | Feasibility/Ethical | Phase 2 mein 50 random questions aap manually grade karo | **≥ 40/50 "sahi aur useful"** (80%) |
| A2 | Mandatory gate se aap tang nahi aoge | Desirability | 7-din dogfood | **≥ 5/7 din** gate complete, uninstall urge nahi |
| A3 | 50 min ke baad 10–30 MCQ ka time (≈ 8–12 min) worth lagega | Desirability | Din ke end mein 1-line survey | ≥ 4/5 "worth it" |
| A4 | Free quota 1 din ke gates + CA ke liye kaafi hai | Feasibility | Quota ledger 7 din | fallback ladder se **0 din** bina quiz |
| A5 | Pet "watching" motivating hai, anxiety nahi | **Ethical** | Mode survey (Coach/Strict/Silent) | Strict mode mein "stress ↑" na ho |
| A6 | Mains LLM evaluator ka score topper-grade copy se consistent hai | Feasibility | Same answer 3× evaluate | **range ≤ ±1.5 marks** (10-marker par) |
| A7 | Human-in-loop Web Assist kaafi hai (full-auto ki zaroorat nahi) | Usability | Friction time measure | ≤ 5 min/day |

## 5. Metrics (HEART)

| Category | Metric | Target (starting hypothesis) |
|---|---|---|
| **H**appiness | Weekly 1-question check-in ("is hafte ka mood/confidence 1–5") | trend ↑ |
| **E**ngagement | Focused sessions / week | ≥ 25 (≈ 5/din) |
| **A**doption | Features used (gate, FSRS, PYQ) | core 3 by week 2 |
| **R**etention | D7 / D30 use (khud ke liye: kya 30 din chala?) | D30 yes |
| **T**ask success | Gate pass rate; due-cards cleared | pass ≥ 70% / due ≥ 80% |
| **North Star** | Verified Retained Minutes / week | baseline pehle 2 hafte, phir +10%/hafta |

**Guardrail metrics (nuksan pakadne ke liye):** sleep-window sessions, ≥ 12h days, "report bad question" rate, skip-gate rate.

## 6. Ethics / Responsibility check (Papanek lens)

| Dimension | Risk | Mitigation |
|---|---|---|
| **Harm** | "Koi dekh raha hai" pet → anxiety, guilt-spiral. Streak loss → quit. | **Modes: Coach (default) / Strict / Silent.** Streak freeze, comeback quest, bad-day mode. Pet kabhi shame nahi karta (language rules). |
| **Harm** | Raat ko late padhna, burnout | Sleep guard, burnout guard, forced rest-day suggestion |
| **Harm** | Galat MCQ/fact yaad ho gaya | Source quote + page, validation, report button, `verified` flag popups ke liye |
| **Harm** | Galat confidence ("predicted score") | Hamesha "practice score" + range |
| **Access** | English-only? | Hindi/English UI (P10), Hindi medium question language option |
| **Access** | Mehengi hardware | Offline/local chhota model, features alag-alag, low-RAM mode |
| **Privacy** | Webcam, screen titles, Telegram session | Sab local. Webcam sirf interview mein, default **store nahi**. Focus Guard opt-in, sirf app-category. Privacy panel dikhaye kya store hai. |
| **Legal** | Copyrighted PDFs | Personal local use; bypass nahi; official sources pehle |
| **Sustainability** | Builder burnout | Phase-gated roadmap; Phase 2 ke baad hi aage |

**Pre-mortem ("1 saal baad ye app nuksan kar gaya, kyun?"):** (1) galat MCQ yaad ho gaye → verification; (2) aap tang aakar band kar diye → modes + emergency skip; (3) free quota band hua, app bekar → local fallback; (4) pet ne shame kiya, mental health bigda → language rules + Silent mode.

## 7. Design principles (DESIGN.md ka summary)

1. **Calm, not childish.** Gamification subtle: progress rings, XP, pet. Cartoonish confetti nahi.
2. **Progress = proof.** Bar tabhi badhe jab recall pass ho (honest coverage).
3. **One primary action per screen** ("Aaj ka next block shuru karo").
4. **Friction sirf wahan jahan learning ho** (gate), baaki jagah zero friction.
5. **Hindi + English dono** achhe se render hon.
6. **Colour ke saath icon** (Green ✓ / Amber ◐ / Red ✕) taaki colour-blind users bhi samjhein.
7. **Keyboard-first** (shortcuts: start/pause/bookmark).

## 8. Screen map (information architecture)

```
Today ─┬─ Next block (CTA) · Due cards · CA digest · Streak/XP · Pet
Study  ─┬─ Library ── Reader (pdf.js) ── Start/End bookmark ── Timer ── Gate
Syllabus ─ Tree (progress bars, heatmap) ── Node detail (books, PYQs, CA, notes)
PYQ Lab ── Drill · Trap stats · Mistake Autopsy · Split-view compare
Mains ──── Questions · Write+Upload · Evaluation report · Handwriting sheet
Current Affairs ── Digest · 35-min mode · Trackers
Interview ── DAF · Room (silent) · Report
Browser ── Allowlisted lectures · AI side panel
Insights ── Truth dashboard · Calibration · Forecast · Honesty report
Settings ── AI routing · Paths · Telegram · Privacy · Pet mode · Rubric editor
```

## 9. Pet communication rules (shame nahi, coach)

| Situation | Do | Don't |
|---|---|---|
| Aap idle ho gaye | "10 min se kuch nahi hua. 2-minute start karein?" | "Phir time waste?" |
| Gate fail | "Ye hissa dobara dekhte hain (p.142)" | "Tum fail ho gaye" |
| Streak toot gayi | "Comeback quest: 1 pomodoro" | "Streak khatam" |
| Raat 1 baje | "So jao, kal gate easy rakhunga" | Study push karna |
| Badi jeet (level-up) | Chhota, specific celebration | Over-the-top confetti |

## 10. Validation plan (research without big effort)
1. **Week 0:** 3 aspirants se 20-min conversation: "pichli baar kab padha aur bhool gaye?" Job map ki scores update karo.
2. **Phase 2 ke baad:** 7-din dogfood (aap khud) + A1/A2/A3 ke criteria.
3. **Phase 3 ke baad:** Pet modes ka A5 test.
4. Har assumption ka result `agents/research/` mein likho.
