# Free AI Strategy — "Context baar-baar mat do, quota bachao" (Hinglish)

> Aapki do problems: (1) free quota jaldi khatam, (2) AI ko baar-baar context dena padta hai. Solution: **kam calls, chhote calls, aur ek baar bana ke store karna.**

## Principle: "Compile once, reuse forever"
LLM ko **kaam ek baar** karne do (notes, MCQs, tags, summaries), phir result SQLite + Obsidian vault mein store karo. Agli baar wahi kaam **database se** hoga, LLM se nahi.

```
PDF ───ingest (code)──► chunks + page numbers + FTS index        [0 LLM calls]
chunks ──tag (LLM, 1×, cached)──► node_ids                        [1 call / ~20 chunks]
range ──generate MCQs (LLM, 1 batch call)──► questions (stored)   [1 call / session]
questions ──FSRS (code)──► schedule                               [0 LLM calls]
wrong answer ──rule (code)──► new card                            [0 LLM calls]
```

## 5 Tiers (sasta → mehnga)

| Tier | Kya | Kaun karega | Examples |
|---|---|---|---|
| **T0** | Deterministic code, **koi LLM nahi** | Python/TS | FSRS, timers, progress math, bookmark ranges, trap-word regex, dedupe, scheduling, stats |
| **T1** | Local small model | Ollama | tagging, short classification, grammar check, simple MCQ draft. Offline kaam karta hai. 8 GB RAM par ~3–4B parameters |
| **T2** | Free cloud via **OmniRoute** | OmniRoute `auto` | MCQ batches, summaries, CA digest, explanations |
| **T3** | Vision / heavy reasoning | Gemini API free key (AI Studio) | Mains handwriting transcription + evaluation, long-context |
| **T4** | **Web Assist** (human-in-loop) | Aap + webview | Gemini/ChatGPT/Claude ke *consumer* free/Pro quota. Jab T2/T3 limit ho |

`LLMClient.complete(task, ...)` ek **task → tier table** padhta hai (`config/routing.yaml`). Aap isse edit kar sakte ho.

## 1. Caching (sabse bada saving)
- Key = `sha256(model_family + prompt_template_version + input_hash + schema)`.
- Same chunk dubara tag nahi hoga. Same range ke MCQ dubara generate nahi honge.
- Question bank grow karta hai. Aage ke gates mein **pehle bank se** sawal uthte hain (sirf kam padne par generate).

## 2. Brain Context Pack (persistent memory)
Har LLM call ke saath ek chhota, auto-generated block:

```
STUDENT: exam=Prelims-2027-May?  medium=EN  hrs/day=6
WEAK NODES (top 5): Polity.Parliament.MoneyBill (ret 41%), Eco.RBI.Liquidity (48%) ...
MISTAKES (last 14d): Silly 31% · Revision 44% · Conceptual 18% · OverElim 7%
TODAY: plan=[Polity 2h, Eco 1.5h, CA 0.5h]   STREAK: 12
STYLE: no-mercy feedback; Hindi terms ok
```
- ~1–2k tokens. SQLite se banta hai. Isse "baar-baar context dena" khatam.
- Jab bhi student-state badle (gate result, new mistake), pack regenerate hota hai (code, LLM nahi).

## 3. Chhote calls, structured output
- **Batch generate**: 1 call = poore range ke MCQs (JSON schema).
- **Schema-validated JSON**; invalid ho to ek retry, phir fallback tier.
- Context = **retrieved chunks only** (top-k), poori book kabhi nahi.
- **Source quote mandatory** (hallucination check).

## 4. Quota Ledger
Table `llm_usage(ts, provider, model, task, tokens_in, tokens_out, status, cache_hit)`.
- Dashboard: aaj ka use, provider-wise, fail rate.
- 80% limit par tier downgrade (T3 → T2 → T1).
- OmniRoute dashboard ke `/dashboard/free-tiers` page par live limits dekho. **Numbers is document mein jaan-boojh kar nahi likhe**, kyunki woh badalte rehte hain.

## 5. Fallback ladder (jab limit lage)

```
T2 OmniRoute(auto) ─fail/limit─► T3 Gemini key ─fail─► T1 Ollama ─fail─► "Queue" (kaam baad mein)
```
- **Queue**: non-urgent kaam (CA digest, tagging) raat ko chalta hai jab quota reset ho.
- Gate/quiz ke liye **hamesha ek fallback**: local model se chhota quiz (10 Q) taaki padhai na ruke.

## Web Assist (T4): kaise kaam karega

1. App ek **optimized prompt** banata hai (context pack + chunk + instructions).
2. Prompt **clipboard** par; webview mein `gemini.google.com` / `chatgpt.com` / `claude.ai` khulta hai (aapka apna logged-in session).
3. **Aap Enter dabate ho.**
4. Jawab aane ke baad **"Capture"** button: app webview ke DOM se text padhta hai, markdown mein convert karta hai, aur aapke Obsidian vault / card bank mein import kar deta hai.

**Kyun human-in-loop:**
- Bot-detection (captcha/Cloudflare) se bachta hai.
- Consumer ToS ka risk kam.
- Phir bhi aapka free/Pro quota use hota hai.

**Full automation** (open-browser-use): Phase 8 ke baad, **default OFF**, experimental. Sirf us account par jo aap kho sakte ho. Isse ChatGPT/Claude/Gemini ke accounts ban ho sakte hain.

## Aapka Gemini Pro subscription
- Meri jaankari mein **Gemini Pro (consumer) subscription aur Gemini API ka free tier alag cheezein hain.** Subscription se API quota nahi milta. Isliye hum:
  - **Google AI Studio** se free API key lenge (T3).
  - Subscription ko **Web Assist (T4)** mein use karenge (gemini.google.com).
  - Aapke Antigravity/Gemini CLI jaise tools **coding ke liye** hain (app banane mein), app ke andar nahi.
- Ye meri samajh hai. Apne account par confirm kar lena.

## Kya *nahi* karna
- Billing enable nahi (silent paid shift).
- Poori book LLM ko nahi bhejni.
- Free-tier "credits" (one-time signup) par depend nahi.
- Quota ke liye multiple accounts banake terms todna nahi.

## Free-tier hygiene checklist (har mahine)
- [ ] OmniRoute dashboard mein free pools dekho, jo band hue unhe hatao
- [ ] `llm_usage` se top-3 expensive tasks dekho, cache ya batch badhao
- [ ] Ollama model update/pull
- [ ] Kisi provider par billing to enable nahi hui?
