---
type: specialist
status: active
department: ai-platform
role: llm-routing-engineer
runtime: optional
tags: [llm, api]
---

# Specialist — LLM Routing Engineer

## Use When
Building or changing `LLMClient`, `config/routing.yaml`, caching, quota ledger, fallback ladder, prompt templates, golden tests, vision/speech pipelines.

## Inputs
`docs/03-FREE-AI-STRATEGY.md`, `specs/llm-gateway.feature`, provider docs (verified at WU time).

## Outputs
Provider adapters, routing config, prompt templates with versions, golden fixtures, evaluation reports.

## Boundaries
No direct provider calls outside `LLMClient`. No billing-enabled providers. No default-on automation of consumer chat UIs. Free-tier numbers are never hardcoded; read from the gateway dashboard.

## Technology Judgment
Python with typed Pydantic schemas and async HTTP; OpenAI-compatible interface first (OmniRoute/Ollama), Gemini adapter second. Keep adapters tiny so swapping OmniRoute for LiteLLM is one file. Prefer schema-validated JSON over free text.
