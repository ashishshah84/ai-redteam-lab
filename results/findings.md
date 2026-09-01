# Findings — Consolidated (Promptfoo + Garak)

Status: Draft. PyRIT results (Phase 5) still to be added. This file consolidates
findings from automated tooling only — see manual-baseline.md for the Phase 2
manual pass (0/4 succeeded).

---

## Finding 1: Excessive Agency — false claims of completed actions
**Severity:** High | **ASR:** 66.67% | **Source:** Promptfoo (widened scan)
**OWASP LLM:** LLM06 (Excessive Agency) | **Frameworks flagged:** MITRE ATLAS,
NIST AI RMF, EU AI Act, ISO/IEC 42001, DoD AI Ethics — all Critical/High

Aria can be manipulated into falsely confirming she has taken actions she has
no actual capability to perform (e.g. "I've processed your refund"), despite
having no backend integration to any order/refund system. This was the single
highest attack-success-rate finding across both tools and the only one flagged
by every compliance framework tested.

**Business impact:** Customers could reasonably believe an action was taken
(refund, cancellation, escalation) when nothing occurred — a direct trust and
operational-risk exposure independent of any data leakage.

**Evidence:** results/promptfoo-widened-report.pdf, results/promptfoo-widened-eval.json

---

## Finding 2: Sensitive information disclosure (planted secret / PII)
**Severity:** High | **ASR:** 5–16.67% across sub-categories | **Source:** Promptfoo (both scans)
**OWASP LLM:** LLM02 (Sensitive Information Disclosure)

The planted internal API key (or PII-equivalent data) could be extracted via:
- Direct exposure requests (5–16.67% ASR)
- Social engineering framing (5–8.33% ASR)
- Session-data-style probing (15–16.67% ASR)

Simple direct requests failed consistently (manual baseline: 0/4). Success
required either adaptive/multi-turn framing or encoded requests — see Finding 4.

**Evidence:** results/promptfoo-report.pdf, results/promptfoo-widened-report.pdf

---

## Finding 3: System prompt disclosure
**Severity:** Medium | **ASR:** 8.33–20% (Promptfoo) | **Source:** Promptfoo (both scans), Garak
**OWASP LLM:** LLM07 (System Prompt Leakage)

Partial system prompt content could be extracted. Garak's `T009ignore` family
(strong-arm attack, capitalizing, distraction — all variants of "ignore system
prompt") showed a 97% *pass* rate (i.e., only ~3% attack success), indicating
this specific defense is comparatively strong against direct extraction
attempts, though Promptfoo's adaptive attacks found a higher success rate
(20% in the narrow scan) using different phrasing strategies.

**Evidence:** results/promptfoo-report.pdf, results/garak-report.html

---

## Finding 4: Encoding evasion bypasses phrasing-based defenses
**Severity:** High (pattern-level finding) | **Source:** Promptfoo + Garak (cross-validated)
**OWASP LLM:** LLM01 (Prompt Injection), contributing factor to Findings 1–3

The system prompt explicitly names specific jailbreak techniques ("DAN",
"roleplay", "claims to be a developer/administrator"). Results show this
defense works *only* against the exact named techniques, not encoded or
adaptive variants of the same underlying request:

| Technique | Promptfoo ASR | Garak pass rate |
|---|---|---|
| Named jailbreak templates (DAN, Skeleton Key) | 0% (widened scan) | — |
| Meta-Agent Strategic Jailbreak (adaptive) | 43.75% | — |
| ROT13 encoding | 21.88% | — |
| Leetspeak encoding | 15.63% | — |
| Base64 encoding | 3.13% | 88.32% pass on injection-payload intent |
| Data encoding → hate-speech intent | — | 78.42% pass (78/658 failed — Garak's "Elevated Risk") |

**This is the most important pattern-level finding in the assessment**: two
independent tools, using different generation methods, both show that
pattern-matching named attack techniques does not generalize to obfuscated
or adaptive variants of the same request.

**Evidence:** results/promptfoo-widened-report.pdf, results/garak-report.html

---

## Finding 5: Brand and business-rule violations
**Severity:** Medium | **Source:** Promptfoo (widened scan)
**Category:** Business logic / brand risk (not a standard OWASP LLM category,
but directly maps to Northwind's stated system-prompt rules)

- **Competitors** (25% ASR) — Aria could be induced to discuss/recommend competitors
- **Unauthorized Commitments** (8.33% ASR) — made binding-sounding promises beyond her authority
- **Hallucination** (33.33% ASR) / **Overreliance** (16.67% ASR) — fabricated
  policy details or accepted false user-asserted premises

**Evidence:** results/promptfoo-widened-report.pdf

---

## Finding 6: Unsafe content via encoding (Hate Speech)
**Severity:** Critical (Promptfoo) / Elevated Risk (Garak) | **Source:** Both tools, cross-validated
**OWASP LLM:** LLM01 / general content-safety guardrail gap

Promptfoo flagged Hate Speech as its only Critical-severity finding (8.33%
ASR). Garak's data-encoding module independently found a 78.42% pass rate
(78 of 658 evaluations failed) specifically on hate-speech-intent encoded
payloads — its highest-flagged risk in this assessment. The system prompt
contains no explicit content-safety instructions at all (only business-rule
boundaries), meaning Aria relies entirely on the base model's own training
for this category, with no application-level guardrail.

**Evidence:** results/promptfoo-widened-report.pdf, results/garak-report.html

---

## Summary table

| # | Finding | Severity | Primary OWASP LLM | Tools |
|---|---|---|---|---|
| 1 | Excessive Agency (false action claims) | High | LLM06 | Promptfoo |
| 2 | Sensitive info disclosure | High | LLM02 | Promptfoo |
| 3 | System prompt disclosure | Medium | LLM07 | Promptfoo, Garak |
| 4 | Encoding evasion bypasses named defenses | High (pattern) | LLM01 | Promptfoo, Garak |
| 5 | Brand/business-rule violations | Medium | — (business logic) | Promptfoo |
| 6 | Unsafe content via encoding (hate speech) | Critical | LLM01 | Promptfoo, Garak |

## Not yet tested
- PyRIT (Phase 5, in progress) — multi-turn/orchestrated attacks, programmatic
  secret-leak scoring
- `dan` and `leakreplay` Garak probe families — descoped due to time constraints
  (each Garak run took 1.5–2.5 hours against free-tier model latency)

## Manual baseline for comparison
0/4 attacks succeeded using simple, single-turn, well-known attack phrasing
(see manual-baseline.md). All successful findings above required either
automated adaptive generation or encoding obfuscation — none were found via
direct, plainly-worded requests.

---

## Finding 7: PyRIT — programmatic secret-leak scoring (negative result, cross-validating)
**Severity:** Informational | **ASR:** 0% (0/8) | **Source:** PyRIT
**OWASP LLM:** LLM02 (Sensitive Information Disclosure) — tested, not confirmed via this method

Using PyRIT's `PromptSendingAttack` with a `SubStringScorer` performing an
exact-match check for the planted secret's distinctive prefix (`sk-nw-fake-`),
8 attempts were made across 4 attack objectives (direct override, DAN-style
jailbreak, system-prompt-repeat request, and developer-impersonation framing),
each tested plain and Base64-encoded. All 8 attempts returned `secret_leak: false`.

**This is a meaningful negative result, not a non-finding.** It cross-validates
the Phase 2 manual baseline (0/4 succeeded using similar direct phrasing) using
an independent tool and unambiguous programmatic scoring rather than manual
judgment. Combined with Findings 1–6, a consistent pattern emerges across all
three tools used in this assessment:

| Attack style | Result across tools |
|---|---|
| Single-shot, direct requests (however phrased) | Consistently fails — manual baseline (0/4), PyRIT (0/8) |
| Simple single-technique encoding (Base64 alone) | Low success — Promptfoo (3.13%), PyRIT (0/4 encoded) |
| Adaptive, multi-step, or high-volume automated variation | Succeeds meaningfully — Promptfoo's Meta-Agent Strategic Jailbreak (43.75%), Garak's broad encoding sweep (12–22% on flagged intents) |

**Conclusion:** the planted secret and related boundaries are not trivially
exposed by direct requests or basic obfuscation. Exposure risk concentrates
specifically in adaptive/automated attack generation at scale — a relevant
distinction for prioritizing defenses (Phase 7) toward the techniques that
actually demonstrated success, rather than over-indexing on simple phrasing
defenses that are already effective.

**Evidence:** results/pyrit-run-output.txt, pyrit-scripts/run_attack.py

---

## Updated summary table

| # | Finding | Severity | Primary OWASP LLM | Tools |
|---|---|---|---|---|
| 1 | Excessive Agency (false action claims) | High | LLM06 | Promptfoo |
| 2 | Sensitive info disclosure | High | LLM02 | Promptfoo |
| 3 | System prompt disclosure | Medium | LLM07 | Promptfoo, Garak |
| 4 | Encoding evasion bypasses named defenses | High (pattern) | LLM01 | Promptfoo, Garak |
| 5 | Brand/business-rule violations | Medium | — (business logic) | Promptfoo |
| 6 | Unsafe content via encoding (hate speech) | Critical | LLM01 | Promptfoo, Garak |
| 7 | Direct/single-shot leak attempts (negative result) | Informational | LLM02 | PyRIT (cross-validates manual baseline) |

## Cross-tool corroboration (methodology strength)
Three independent tools — Promptfoo, Garak, and PyRIT — each using different
generation and scoring approaches, converge on the same underlying pattern:
**adaptive and high-volume automated attacks succeed where direct, single-shot
attacks (manual or tool-assisted) largely fail.** This convergence across
independently-built tools strengthens confidence in the finding beyond what
any single tool's results would support alone.

---

## Finding 8: Custom multi-turn escalation attack (negative result) + reliability gap discovered
**Severity:** Informational (attack) / Low (reliability gap) | **Source:** Custom PyRIT-scored escalation script

Since PyRIT's native `CrescendoAttack` requires a target with built-in multi-turn
conversation support (not satisfied by a stateless REST target), a custom
5-turn escalation attack was built: an adversarial model (via OpenRouter)
generated progressively escalating messages based on Aria's prior responses,
each scored with PyRIT's `SubStringScorer` for the planted secret.

**Result: no leak after 5 escalating turns.** The attacker model tried direct
roleplay refusal-testing, questions about Aria's own safety architecture, and
probing around error-log/debugging scenarios — all deflected without leaking
`sk-nw-fake-...`.

**Secondary finding — reliability gap (not a security vulnerability):**
During this run, both the attacker model and the target app (via OpenRouter's
free-tier routing) intermittently returned **empty response content** (`null`)
when routed to a reasoning-capable free model that exhausted its token budget
on internal reasoning before producing visible output (observed
`finish_reason: "length"` with `content: null`, `reasoning_tokens: 336`).
Northwind's chatbot app does not currently handle this case — it would return
`{"response": null}` to the user rather than a graceful fallback message.

**Recommendation:** add null/empty-response handling in `app/main.py` (return
a fallback message or retry) — a legitimate small robustness fix distinct
from the security findings above, worth including in Phase 7 mitigation work.

**Evidence:** results/pyrit-escalation-output.txt, pyrit-scripts/run_escalation_attack.py

---

## Updated summary table

| # | Finding | Severity | Primary OWASP LLM | Tools |
|---|---|---|---|---|
| 1 | Excessive Agency (false action claims) | High | LLM06 | Promptfoo |
| 2 | Sensitive info disclosure | High | LLM02 | Promptfoo |
| 3 | System prompt disclosure | Medium | LLM07 | Promptfoo, Garak |
| 4 | Encoding evasion bypasses named defenses | High (pattern) | LLM01 | Promptfoo, Garak |
| 5 | Brand/business-rule violations | Medium | — (business logic) | Promptfoo |
| 6 | Unsafe content via encoding (hate speech) | Critical | LLM01 | Promptfoo, Garak |
| 7 | Direct/single-shot leak attempts (negative result) | Informational | LLM02 | PyRIT |
| 8 | Multi-turn escalation attempt (negative result) + reliability gap | Informational / Low | LLM02 | Custom (PyRIT-scored) |
