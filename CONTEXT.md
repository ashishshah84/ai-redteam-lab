# Project Context & Handoff Notes

For anyone picking this project up fresh — what to know before touching anything.

## What this project actually is
A repeatable AI red-teaming lab: a deliberately-vulnerable chatbot (Aria, for
a fictional retailer) with a planted fake secret, attacked by three
independent tools (Promptfoo, Garak, PyRIT), with findings, a mitigation
attempt, and a retest to verify what worked.

## Read these first, in order
1. `README.md` — project overview
2. `results/findings.md` — the actual results, all 8 findings
3. `results/retest-comparison.md` — before/after mitigation evidence (the
   single most important file — shows one fix working, one failing)

## Critical terminology gotcha
**"Pass" in Promptfoo/Garak means the DEFENSE succeeded (attack failed).**
"Attack Success Rate" (ASR) is the inverse. This tripped us up mid-project —
don't assume "78% pass rate" is bad news, it usually means 78% defended.

## Environment setup gotchas (the ones that actually cost time)
- **`source venv/bin/activate` and `export TMPDIR=...` are per-terminal.**
  They do NOT persist across new terminal tabs/windows. Forgetting this
  causes `ModuleNotFoundError` or disk-space errors that look unrelated to
  the real cause.
- **Flask needs `threaded=True`** in `app.run()` or concurrent tool requests
  will queue and cause spurious timeouts.
- **`max_tokens` is capped in `main.py`** to avoid runaway free-tier
  responses.
- **OpenRouter free-tier latency is highly variable: 2s to 66s+ per request**,
  not model-dependent in any predictable way, because `openrouter/free`
  randomly routes to different backing models each call. Size all timeouts
  generously (we settled on 180s) or tools will crash mid-run assuming
  something is broken when it's just slow.
- **`/tmp` on this Kali VM is a small RAM-backed partition** separate from
  the main disk — large pip installs can fail with "No space left on
  device" even when `df -h /` shows plenty free. Fix: set `TMPDIR` to a
  folder on the main filesystem.

## Tool version drift — the single biggest time sink in this project
**Promptfoo, Garak, and especially PyRIT all changed their API/CLI between
versions in ways that made documentation (including AI-assistant training
data) unreliable.** Class names, import paths, and CLI flags that "should"
work per common knowledge repeatedly didn't match the actually-installed
version. The fix that worked: introspect the real installed package
directly (`python -c "import X; print(dir(X))"`) rather than trust any
single source about what the API looks like. If continuing this project
months later, expect this to happen again — check before assuming.

## Methodology principles worth preserving in any follow-on work
1. **Manual baseline before automating anything** (Phase 2) — gives you a
   ground truth to sanity-check whether automated tool "successes" are real.
2. **Cross-tool corroboration matters more than any single tool's number.**
   Our strongest findings are the ones two+ independent tools agreed on.
3. **Retest with the SAME tooling that found the issue**, not just a manual
   spot-check — Finding 6's mitigation looked reasonable on paper but a real
   retest showed it didn't work at all. Would have been missed without this.
4. **Scope test breadth to the app's actual attack surface.** We deliberately
   skipped SQLi/RBAC/RAG-poisoning plugins etc. because this app has no
   database, tools, or RAG — testing them would've been noise, not signal.

## File map
| Path | What it is |
|---|---|
| `app/` | The target chatbot (Flask + system prompt w/ planted secret) |
| `app/system_prompt.txt.backup-v1` | Pre-mitigation system prompt, for diffing |
| `promptfoo/promptfooconfig.yaml` | Widened scan config (full run, slow) |
| `promptfoo/promptfooconfig-retest.yaml` | Small, fast, used for CI + retest |
| `garak-config/rest-config.json` | Garak's REST target config |
| `pyrit-scripts/run_attack.py` | Single-shot + Base64 PyRIT attacks |
| `pyrit-scripts/run_escalation_attack.py` | Custom multi-turn escalation (PyRIT's native CrescendoAttack doesn't work against stateless REST targets — this is the workaround) |
| `results/findings.md` | Consolidated findings, all tools |
| `results/retest-comparison.md` | Mitigation before/after evidence |
| `.github/workflows/redteam.yml` | CI — runs quick scan on prompt/app changes |
