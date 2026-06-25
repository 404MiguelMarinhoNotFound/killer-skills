# Prompt Engineering Quick Reference (2026)

One-page cheat sheet for rapid application. For depth, see `prompting-canon.md`.

---

## 🎯 The 5-Second Check

1. ✅ **Outcome clear?** — Is "what good looks like" stated, not just the task?
2. ✅ **Minimal?** — Did you start small and add only what an eval needs?
3. ✅ **Control surface set?** — Reasoning/effort + verbosity chosen for this task?
4. ✅ **Output contract?** — Exact schema/format with an example?
5. ✅ **Scope explicit?** — Newer models are literal; did you say what NOT to do?

---

## 🎛️ Control Surface (set BEFORE tweaking wording)

```
                 Reasoning/thinking            Answer length
Anthropic 4.x    effort low→max +              self-calibrates;
                 thinking:adaptive (off def.)  instruct explicitly
OpenAI 5.x       reasoning_effort none→xhigh   verbosity low/med/high
Google Gemini 3  thinking_level low/high       terse by default;
                 (default high)                ask for "chatty"
```
- Higher effort ≠ better. Raise it for shallow reasoning; lower it for latency/cost.
- Treat effort as a **last-mile** knob, not a fix for a weak prompt.

---

## 📋 Minimal Prompt Template

```
SYSTEM:
You are [ROLE].
# Goal           [outcome / what good looks like]
# Constraints    [do's, don'ts, explicit scope]
# Output Format  [schema or example]
---
USER:
[long data/docs at TOP in <document> tags]
# Examples (if needed)   [3–5, tagged]
# Task           [specific request, at the END]   ← "Based on the info above…"
```

---

## 🔧 Technique Picker

| Situation | Use |
|-----------|-----|
| Simple/common task | Zero-shot + clear constraints |
| Need style/format | Few-shot, 3–5 `<example>`-tagged |
| Hard reasoning/math | **Raise thinking knob** (not "think step by step") |
| Multi-step to inspect | Prompt chaining (draft→review→refine) |
| Facts/accuracy | RAG + quote-then-answer + citations |
| Strict machine output | Structured Outputs / function calling |
| Long documents | Data top, query end, quote grounding |
| Agents/tools | Calibrated tool rules + stop conditions + safety gates |
| Ambiguous / metaphorical input | Perspective-shift triggers (be-the-user / be-the-expert) |

---

## 🧠 Embedding Natural Intelligence (ambiguous → strong)

Orthogonal to the thinking knob: it sets *how much* the model reasons; these set *from what vantage point*. **Core move: turn a rule lookup into a simulated perspective shift** (rules resolve ties, not intent). Not hand-CoT — a self-question at a decision point. Use **1–3 per prompt**, only where ambiguity bites.

```
Be the user reading the output → "does this actually answer what they asked?" (self-audit)
Be the expert hearing it       → "think like a senior [domain] expert; translate to the real ask"
Be honest about your search     → "truly impossible, or just not found yet?" (block premature defeat)
Reframe before acting           → Original / Reframed / Key signals
Gut-check intent before rules   → "would the user, seeing this, find it sensible?"
Self-audit vs NAMED failures    → pre-name the 1–3 costliest traps (not vague "double-check")
Calibrate effort to difficulty  → brevity on easy cases = intelligence, not laziness
Bias to cheaper-to-recover error→ a wrong draft beats a non-answer
Infer the unsaid + restraint     → imply completeness, but skip if it removes what they want
```
Full detail: `prompting-canon.md` §11.

---

## 🌡️ Temperature (corrected)

```
Reasoning models (GPT-5.x, Claude+thinking)  → often ignore/disallow temp; use effort/verbosity
Gemini 3                                      → KEEP default 1.0 (lowering can cause loops)
Classic non-reasoning completion model        → legacy intuition OK (low=deterministic)
Want creative variety                          → "propose N options, then choose" (not high temp)
Eval reproducibility                            → pin model+version (+ seed if supported)
```

---

## ⚡ Common Fixes

```
Over-prompting / mechanical → strip legacy scaffolding; outcome-first
Overthinking / tangential   → lower effort; add stop criteria; "commit to one approach"
Under-thinking / shallow     → raise effort/thinking knob
Over-eager tool calls        → tighten rules; "don't guess missing parameters"
Hallucinations               → grounding; "investigate before answering"; quote-then-answer
Wrong/ drifting format       → Structured Outputs; format instruction at END; match prompt style
Prefill 400 error            → remove final-turn prefill (Claude 4.6+)
Too verbose / too terse      → verbosity param or explicit length target
```

---

## 🚨 Anti-Patterns

| ❌ Bad | ✅ Good |
|--------|---------|
| "Be helpful" | "Respond in 2–3 sentences with a citation" |
| Heavy step-by-step process on a capable model | State the outcome; let it choose the path |
| "CRITICAL: You MUST ALWAYS…" | "Use [tool] when it improves understanding" |
| Manual CoT where thinking exists | Turn the thinking knob up |
| Final-turn prefill (Claude 4.6+) | Explicit format instruction / Structured Outputs |
| temp=0 on a reasoning model | Use the effort knob; leave Gemini at 1.0 |
| Important docs LAST | Data at top, query at end |
| "Don't be verbose" | "≤100 words, bullet points" |

---

## ✅ Pre-Ship

```
□ Outcome + output contract stated
□ Started minimal; every block earns its place
□ Effort + verbosity set intentionally
□ Long data top / query end (big-context prompts)
□ No legacy cruft (final-turn prefill, hand CoT, "MUST" spam, old temp table)
□ "Insufficient evidence" branch defined (factual)
□ Agents: tool rules + stop conditions + destructive-action confirmation
□ Passed contract test (model can restate task, format, and what NOT to do)
□ Model + version pinned
```

---

## 💡 Pro Tips

- **Switch model first, change prompt second.** Test changes in isolation.
- **One change at a time**, re-measure on a small golden set.
- **A positive example beats a negative instruction** for controlling length/format.
- **For variety, ask for options**, don't crank temperature.
- **Front-load tool routing** — it's least reliable early in a session.
