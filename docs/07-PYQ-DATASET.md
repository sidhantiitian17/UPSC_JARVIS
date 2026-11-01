# PYQ Dataset — official UPSC site se Markdown dataset (Hinglish)

> Status (2026-11-01, owner laptop): **fetch works** (99 English PDFs, `www.upsc.gov.in` + `/archives`). **98 of 99 PDFs are image-only, so parsing needs OCR (Tesseract not installed yet).** Only 2023 Prelims GS-I has a text layer (10/~100 questions parsed). Neeche §9 purani cloud-sandbox history hai.

## 1. Goal
UPSC ki official site ke saare **previous year question papers** download karke ek **verified, versioned, Markdown dataset** banana:
- **Prelims:** GS Paper I + CSAT (Paper II)
- **Mains:** GS I–IV, Essay
- **Optional: Sociology** Paper I & II (aapka optional)
- (Language/qualifying papers skip, jab tak aap na bolo.) **English medium** → sirf English files; Hindi files `manifest` mein `lang: hi, skipped` ke roop mein record.

## 2. Source of truth (aur kya *nahi* use karenge)
- **Official page:** `https://upsc.gov.in/examinations/previous-question-papers` (URL ek open-source scraper `realyuvishere/upsc-pyq` ke README/code se confirm hua; **site khud maine abhi nahi dekhi**).
- Us scraper se pata chala page ka structure (jab author ne likha): **saal ke hisaab se grouping → table caption mein exam ("Civil Services (Preliminary/Main) Examination") → rows mein category (Optional, Literature, Compulsory Language, General Studies, General) → har row mein PDF links.** Site badal sakti hai. Hamara fetcher ye sab *runtime par* verify karega, aur structure na mile to loudly fail karega.
- **Third-party "PYQ" repos/sites ko source nahi banayenge.** Example: `vinaykumargb/UPSC-Mains-PYQs` ka description khud kehta hai *"Generated using Claude AI"*; `Shabber10/ALL-PYQ-Papers`, `sk417/UPSC-PYQ` jaise repos ke PDFs ka origin unverified hai. **Provenance rule:** har question ka `source_url` official domain par hona chahiye.
- `realyuvishere/upsc-pyq` (MIT, 1★, ~2.9 GB size kyunki usme PDFs commit hain): **reference ke taur par padha**, clone nahi kiya. Uski limits: resume nahi, hash nahi, `robots.txt` check nahi, retry nahi, sirf 1s sleep. Hum apna fetcher likhenge.

## 3. Legal / publishing policy (zaroori)
| Cheez | Policy |
|---|---|
| **Aapka GitHub repo PUBLIC hai** (API se verify: `visibility: public`) | PYQ PDFs ya dataset md ko public repo mein commit karna = redistribution. UPSC ki content/copyright policy maine **padhi nahi** (site blocked). |
| Raw PDFs | **Kabhi commit nahi.** `datasets/pyq/raw/` hamesha `.gitignore`. |
| Generated md dataset | **Owner ne opt-in kiya (2026-11-01):** md/keys/syllabus/reports commit honge; owner sab kaam ke baad repo **private** karega. **Dhyan:** public rehte waqt jo commit hua wo git history/forks/caches mein rehta hai, private karne se purana copy gayab nahi hota. Agar ye matter karta hai to dataset commits hata kar history rewrite karni padegi. UPSC policy ab bhi padhi nahi gayi. |
| Fetcher behaviour | `robots.txt` padhe, `User-Agent` apna naam batayega, **kam rate** (≥ 2 s delay, 1 connection), resume, **koi login/captcha bypass nahi** |
| Personal use | Padhai ke liye local copy; third-party ko redistribute nahi |

## 4. Folder layout
```
datasets/pyq/
  README.md                       # kaise chalayein, status
  manifest.jsonl                  # 1 line / source PDF (git-tracked: sirf URLs+hash, content nahi)
  raw/                            # PDFs — gitignored (never committed)
  md/                             # generated dataset — committed (owner opt-in, §3)
    prelims/2024/gs-paper-1.md
    prelims/2024/csat.md
    mains/2024/gs-1.md  gs-2.md  gs-3.md  gs-4.md  essay.md
    optional/sociology/2024/paper-1.md  paper-2.md
  keys/                           # official answer keys (agar site par mile)
  reports/coverage.md             # kaun sa saal/paper mila, kaun sa missing/failed
  reports/review-sample.md        # owner ke spot-check ke liye
  schema/                         # JSON Schemas (neeche §5)
tools/pyq/                        # fetch / extract / parse / validate (Python, uv)
```

## 5. File format (Markdown + machine-readable YAML)

### 5.1 File-level front matter
```yaml
---
dataset: upsc-pyq
schema_version: 1
exam: cse                 # cse
phase: prelims            # prelims | mains
year: 2024
paper: gs-paper-1         # gs-paper-1 | csat | gs-1..4 | essay | sociology-1 | sociology-2
paper_title: "General Studies Paper I"
lang: en
source_url: "https://upsc.gov.in/…/<file>.pdf"   # exactly jaisa manifest mein
source_sha256: "<hex>"
retrieved_at: "2026-11-01T00:00:00Z"
page_count: 24
parser: "tools/pyq 0.1.0"
question_count: 100
expected_question_count: 100      # warning-level check, fail nahi
verified_count: 0                 # owner ke verify karne par badhta hai
---
```

### 5.2 Per-question block (Prelims example)
````markdown
## Q1
```yaml
id: PRE-2024-GS1-001
phase: prelims
year: 2024
paper: gs-paper-1
number: 1
page: 3
marks: 2                 # paper ke instructions page se; na mile to null
negative_marks: 0.66     # same
answer: null             # official key se; warna null
answer_source: none      # official-key | owner-verified | none
suggested_answer: null   # LLM guess ho to yahan, label unverified, GATE/score mein kabhi use nahi
status: parsed           # parsed → reviewed → verified   (| failed)
tags: []                 # syllabus nodes — baad mein (H1)
```
**Question.** With reference to …, consider the following statements:

1. …
2. …

Which of the statements given above is/are correct?

- (a) 1 only
- (b) 2 only
- (c) Both 1 and 2
- (d) Neither 1 nor 2
````

### 5.3 Mains / Sociology (multi-part)
```yaml
id: MAINS-2023-GS2-014
phase: mains
paper: gs-2
number: 14
marks: 15
word_limit: 250
parts: []                # Sociology: [{label: a, marks: 10, text: "…"}, {label: b, marks: 20, text: "…"}]
section: null            # Sociology: A | B
answer: null             # model answer nahi; PYQ sirf question hai
status: parsed
tags: []
```

### 5.4 JSON Schema (validator ke liye)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "UPSC PYQ question",
  "type": "object",
  "required": ["id", "phase", "year", "paper", "number", "status", "answer_source"],
  "properties": {
    "id": {"type": "string", "pattern": "^(PRE|MAINS|OPT-SOC)-[0-9]{4}-[A-Z0-9]+-[0-9]{3}$"},
    "phase": {"enum": ["prelims", "mains", "optional"]},
    "year": {"type": "integer", "minimum": 1979, "maximum": 2100},
    "paper": {"type": "string"},
    "number": {"type": "integer", "minimum": 1},
    "page": {"type": ["integer", "null"]},
    "marks": {"type": ["number", "null"]},
    "negative_marks": {"type": ["number", "null"]},
    "word_limit": {"type": ["integer", "null"]},
    "section": {"type": ["string", "null"]},
    "parts": {"type": "array", "items": {"type": "object", "required": ["label", "text"]}},
    "answer": {"type": ["string", "null"], "pattern": "^[abcd]$"},
    "answer_source": {"enum": ["official-key", "owner-verified", "none"]},
    "suggested_answer": {"type": ["string", "null"]},
    "status": {"enum": ["parsed", "reviewed", "verified", "failed"]},
    "tags": {"type": "array", "items": {"type": "string"}}
  },
  "allOf": [
    {"if": {"properties": {"phase": {"const": "prelims"}}},
     "then": {"required": ["page"]}},
    {"if": {"properties": {"answer": {"type": "string"}}, "required": ["answer"]},
     "then": {"properties": {"answer_source": {"enum": ["official-key", "owner-verified"]}}}}
  ]
}
```
(Ye draft hai. WU-P00-003 mein spec-first tests ke saath finalize hoga; real PDFs dekhne ke baad `year` ki lower bound, Sociology id prefix, etc. adjust honge.)

## 6. Pipeline (5 stages, har stage idempotent)

| Stage | Kaam | Kaise | Fail hone par |
|---|---|---|---|
| 1. **Fetch** | Listing page parse → PDF links → download | `requests/httpx`, `robots.txt`, ≥ 2 s delay, resume (ETag/Last-Modified), sha256, `manifest.jsonl` | Structure badli → loud error + saved HTML snapshot |
| 2. **Extract** | PDF → page-wise text | `pdfplumber` (MIT) / `pypdfium2` (license WU mein verify; GitHub metadata `None` dikha) | **Scanned detect** (chars/page low) → OCR path |
| 2b. OCR path | Scanned PDFs | `OCRmyPDF` (MPL-2.0, Tesseract) printed text ke liye; doosra opinion Gemini vision (cloud, `LLMClient` ke through) | `status: failed`, manual review |
| 3. **Parse** | Text → questions | Deterministic regex (question numbering, `(a)–(d)`, marks lines). LLM sirf *failed segments* repair kare, **aur parsed text source text ka substring/near-match hona zaroori** | `failed` + report |
| 4. **Validate** | Schema + counts + continuity | JSON Schema; question numbers 1..N continuous; har Prelims Q ke 4 options; duplicates nahi; expected counts (GS-I ~100, CSAT ~80; **warning**, fail nahi) | coverage report mein flag |
| 5. **Review** | Human verify | `reports/review-sample.md`: random **10%** + saare flagged items, PDF-page text vs parsed side-by-side. Owner `status: verified` set kare | verified nahi to gate/training mein "gold" nahi |

**Answer keys:** fetcher official site par key section dhoondega. Na mile to `answer: null`. **LLM se answer nikalna allowed hai sirf `suggested_answer` ke roop mein, `unverified`; gate/scoring/training gold mein kabhi nahi.** Owner ek trusted source se `owner-verified` kar sakta hai.

## 7. Quality gates (Phase 0 exit)
| Check | Target |
|---|---|
| Provenance | 100% questions ka official `source_url` + `source_sha256` |
| Parse accuracy (owner spot-check, 100 random Prelims Q) | **≥ 98/100** exact (stem + 4 options) |
| Mains/Sociology spot-check (50 random) | **≥ 47/50** |
| Count checks | har paper `question_count` vs expected → mismatch ya to explained ya fixed |
| Coverage report | har (year × paper) ke liye: fetched / parsed / verified / failed |
| Reproducibility | `tools/pyq run` do baar chalane par same hash/outputs |

## 8. Dataset ke aage ke use
| Use | Phase |
|---|---|
| PYQ Lab corpus (trend, split-view, trap stats) | P4 (ab P0 ka output consume karta hai) |
| Laya/baseline **gold evaluation set** (H1 tagging, H4 directive, H5 traps, H6 format) | P0 bake-off |
| Sociology optional: Mains Studio, question bank | P5 |
| Distractor Notes (Prelims options) | P4 |
| Next-year "hypothesis" predictor | P4 |

## 9. Blocker aur do raste

**Blocker (2026-11-01, teesri baar check kiya):** Network policy ab theek hai (owner ne environment badla; proxy `CONNECT 200` deta hai): `huggingface.co` 200, `pib.gov.in` 301, `rbi.org.in`, `isro.gov.in`, `prsindia.org`, `india.gov.in` reachable. **Par `upsc.gov.in` TLS handshake par connection reset karta hai (TLS 1.2/1.3, plain HTTP, `www` sab par) aur `ncert.nic.in` jawab nahi deta**: ye site-side hai (is cloud IP ko filter), policy nahi, aur bypass nahi karenge. Dusre Indian gov sites chal rahe hain, to ye sab-India block nahi hai. Proxy status mein ab `ws_closed_mid_exchange` entries hain (tunnel khula, upar ka server band), `connect_rejected` nahi.

| Rasta | Kaise | Tradeoff |
|---|---|---|
| ~~A. Network allow karo~~ **(ho chuka, par kaafi nahi)** | Owner ne environment ki Network access badli; PIB/RBI/ISRO/HF ab khulte hain. `upsc.gov.in` phir bhi site-side reset deta hai. | Is cloud se PYQ nahi aa sakte |
| **B. Aapke Windows laptop par (ab recommended)** | `tools/pyq` ready (35 tests, synthetic fixtures). `cd tools\pyq; uv sync; uv run pyq --out ..\..\datasets\pyq run`. Real-PDF parsing issues ek-do round mein fix honge: laptop se aaye `reports/coverage.md` + `snapshots/` mere paas aane par main parser test-first theek karunga. | Mere paas real PDFs par testing tab tak nahi |

Dono ho sakte hain. **Main A ko prefer karunga**, kyunki parser real PDFs ke bina "no vibe" ke against hai (meri assumptions test nahi hongi).

## 10. Work Units
`agents/roadmap/PHASE_0.md` mein: WU-P00-001 (fetch) … 007 (review sample), aur `specs/pyq-dataset.feature` mein Gherkin.
