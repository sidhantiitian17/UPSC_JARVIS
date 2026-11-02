# OmniRoute setup (free AI gateway, Windows)

OmniRoute (`diegosouzapw/OmniRoute`, MIT, npm package `omniroute`) is a **router**: it listens on
`http://127.0.0.1:20128/v1` and forwards to the AI accounts you connect. It does **not** create free AI by itself:
you must connect at least one provider (for example a Gemini API key). Without one, requests fail.

What was checked in the build container (Linux, omniroute 3.8.52): `npm install` works (about 460 MB unpacked, 3 min),
`omniroute serve` starts, `GET /api/health` returns ok, `GET /v1/models` answers **401 without a key**, and a chat
request with no connected provider answers HTTP 502 (the keyless pool was closed or needed a browser). JARVIS treats
that 502 as "unavailable" and moves on to the next provider in `config/routing.yaml`.
**Not checked:** Windows install, the dashboard screens (steps below follow OmniRoute's README), and a real provider call.

## Steps
1. Install (Node 22+): `npm install -g omniroute@3.8.52`.
   If npm warns about blocked install scripts, run the `npm config set allow-scripts=...` line printed by that warning, then install again.
2. Set your own dashboard password **before the first start** (PowerShell):
   `$env:INITIAL_PASSWORD = "choose-a-password"; omniroute serve`
   The dashboard opens at <http://localhost:20128>. Keep it on this PC only; do not expose the port.
3. Dashboard, **Providers**: add one provider with your own account or API key. Easiest: paste a Google AI Studio Gemini key.
   Or from a terminal:
   `omniroute setup --add-provider --provider gemini --api-key <KEY> --non-interactive --test-provider`
   Free tiers can need signup, approval or a payment method. Check the provider's current terms.
4. Dashboard, **Endpoints**: copy your **OmniRoute key**.
5. In JARVIS: **Settings, AI providers, omniroute**: paste that key, Save, then press **Test AI**.
   The model `auto` is already set in `config/routing.yaml`.

## How JARVIS uses it
`gate_mcq` tries omniroute first, then Gemini directly, then Ollama. `tag_chunk` and `ping` try Ollama first.
If OmniRoute is not running, JARVIS simply falls through to the next provider; nothing breaks.
Start OmniRoute before JARVIS (`omniroute serve`), or use Gemini directly and skip OmniRoute entirely.
