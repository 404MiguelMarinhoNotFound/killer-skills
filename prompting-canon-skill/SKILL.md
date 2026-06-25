---
name: prompting-canon
description: Apply current prompt-engineering best practices from Anthropic (Claude), OpenAI (GPT-5 family), and Google (Gemini 3). Use when crafting or improving prompts, debugging poor AI output, choosing reasoning/verbosity settings, designing agentic or tool-using workflows, or reviewing prompts before deployment. Also use when a prompt must handle ambiguous, metaphorical, or under-specified input and you need the model to reason like a domain expert — embedding "natural intelligence" via introspective triggers, self-audits, perspective shifts, and intent gut-checks rather than mechanical rule-following.
license: MIT
metadata:
  author: prompt-engineering-community
  version: "2.1"
  updated: "2026-06"
  tags: [prompt-engineering, llm, ai, best-practices, anthropic, openai, google, claude, gpt, gemini, agentic, context-engineering, introspection, reasoning-triggers, natural-intelligence]
  sources: [anthropic-docs, openai-gpt5-guides, google-gemini-docs, promptingguide.ai]
---

# The Prompting Canon

## Overview

Expert prompt-engineering guidance consolidated from the **current** official guides of Anthropic, OpenAI, and Google, plus durable patterns from PromptingGuide.ai. It helps you craft effective prompts, pick the right reasoning/verbosity settings, design agentic workflows, debug quality issues, and apply the right technique per task.

> **Two ideas drive this edition:**
> 1. **Reasoning is now a parameter, not a prompt.** Don't fake "think step by step" — set an effort/thinking knob and let the model self-budget.
> 2. **Less is more.** Modern models are hurt by the heavy, over-specified prompts older models needed. Start minimal; add structure only when an eval tells you to.

## When to Use This Skill

- **Craft or improve prompts** for any current LLM (Claude, GPT-5.x, Gemini 3)
- **Choose settings** — reasoning effort, thinking mode, verbosity
- **Debug poor output** — vague, over-eager, overthinking, hallucinated, format-drifting
- **Design agentic workflows** — tool use, subagents, long-horizon state, context engineering
- **Apply a technique** — few-shot, RAG/grounding, chaining, structured outputs
- **Review prompts** before deployment (contract test, eval discipline)

## Core Principles

1. **Clarity over cleverness.** State task, audience, tone, constraints, output format, success criteria. *Golden rule:* if a colleague with no context would be confused, the model will be too.
2. **Outcome over process.** Describe what "good" looks like and the constraints that matter; leave the model room to choose the path. Don't port heavy old scaffolding to a new model.
3. **Tune the control surface first.** Many "quality problems" are an effort knob set too low (under-thinking) or too high (overthinking) — not a wording problem. Treat effort as a *last-mile* knob, not a fix for a bad prompt.
4. **Iterate empirically, one change at a time.** Switch model → pin effort → run evals → tune prompt incrementally.
5. **Know the limits.** Missing knowledge → RAG/tools/fine-tune; format guarantees → Structured Outputs; latency → lower the thinking knob/smaller model; hallucination → grounding + "investigate before answering."

## The Control Surface (set these before fiddling with wording)

| Vendor | Reasoning/thinking | Answer length | Quick guidance |
|--------|--------------------|---------------|----------------|
| **Anthropic (Claude 4.x)** | `effort` low→max; `thinking:{type:"adaptive"}` (off by default) | self-calibrates; instruct explicitly | Start `xhigh` for coding/agentic, `high` for most work |
| **OpenAI (GPT-5.x)** | `reasoning_effort` none→xhigh | `verbosity` low/med/high (separate from thinking) | Set effort explicitly; low/medium handle a lot |
| **Google (Gemini 3)** | `thinking_level` low/high (default high) | terse by default | Keep `temperature=1.0`; ask for "chatty" if needed |

Higher effort is **not** automatically better — with weak stop conditions or open-ended tools it causes overthinking. Raise it to cure shallow reasoning; lower it for latency/cost.

## Essential Prompt Structure (start minimal — drop what you don't need)

```
SYSTEM:
You are [ROLE].                       # one sentence steers tone/focus

# Goal            [crisp outcome — what "good" looks like]
# Constraints     [do's, don'ts, explicit scope — models are literal now]
# Output Format   [schema / example / strict JSON]

---
USER:
[Long data/docs at TOP, in <document> tags]   # for big-context prompts
# Examples (if needed)   [3–5, relevant + diverse, in <example> tags]
# Task            [specific request — at the END, after the data]
```

For long context: **data at the top, query at the end**, anchored with "Based on the information above…" (can improve quality up to ~30% on multi-doc inputs).

## Key Techniques (current status)

- **Zero-shot** — default for simple/common tasks on capable models.
- **Few-shot** — 3–5 relevant, diverse, `<example>`-tagged demos. Highest-leverage addition for style/format.
- **Chain-of-Thought — DEMOTED.** If the model has a thinking mode, use it instead. Manual CoT is a fallback only when thinking is OFF. Keep "verify before finishing" — it still catches errors.
- **Prompt chaining** — mainly for the self-correction pattern (draft → review → refine) when you need to inspect intermediate output.
- **RAG / grounding** — answer only from provided context; quote-then-answer; require citations; define the "insufficient evidence" branch.
- **Role prompting** — role in system, task in user.
- **XML tags** — structure mixed instructions/data; for Gemini, pick XML *or* Markdown, don't mix.
- **Structured Outputs** (was "JSON mode") — use the vendor's strict-schema/function-calling feature for hard format guarantees.
- **Prefilling — LEGACY.** Final-turn prefill is **rejected (400) on Claude 4.6+**. Use explicit format instructions or Structured Outputs instead.
- **Multimodal** — treat each modality as an equal-class input; reference images by number; use a crop/zoom tool when available.

## Agentic & Context Engineering (now central)

- **Calibrate tool use** — drop "always/if in doubt, use [tool]" (causes over-triggering); use "Use [tool] when it improves understanding." Be explicit when you want *action* vs *suggestions*.
- **Parallel tool calls** — encourage for independent calls; never parallelize dependent ones or guess missing params.
- **Long-horizon state** — structured test/task files + freeform progress notes + git as a state log; emphasize incremental progress.
- **Multi-context-window** — different first-window setup prompt; lock down tests; prefer fresh window + re-orient from files/git over compaction; exploit context awareness.
- **Subagents** — delegate parallel/isolated workstreams; work directly for simple/sequential tasks (watch for over-spawning).
- **Autonomy vs safety** — free rein on local/reversible actions; **confirm before** destructive/irreversible/shared-system actions.
- **Curb overengineering** — "only changes directly requested or clearly necessary; validate only at boundaries; no speculative abstractions."
- **Anti-hallucination** — "never speculate about code you haven't opened; read referenced files before answering."

Full detail: `references/prompting-canon.md` §5.

## Embedding Natural Intelligence (introspective triggers)

The thinking knob (§ Control Surface) governs *how much* a model reasons. This is the orthogonal lever: *from what vantage point* it reasons. On ambiguous tasks — where a literal reading gives a technically-correct but useless answer — these triggers turn a mechanical rule-follower into something that behaves like a thoughtful expert.

**Core move:** convert a *rule lookup* into a *simulated perspective shift*. The rule still exists — it resolves ties, not intent. This is **not** hand-written CoT (that prescribes steps); a trigger prescribes a *question the model asks itself at a decision point*, then lets it choose its own path. Reserve **1–3 per prompt**, placed exactly where ambiguity bites — more is over-prompting.

The toolkit (load-bearing first):
- **Be the user reading your output** — self-audit the draft *as the asker*: "does this actually answer what they asked, at the right grain/shape/scope?" before any mechanical check.
- **Be the expert hearing the question** — "think like a senior [domain] expert and translate this into the precise [artifact] it calls for."
- **Be honest about your own effort** — before declaring defeat: "is it truly impossible, or have I just not found it yet?"
- **Reframe ambiguous → precise first** — surface the trace: `Original / Reframed / Key signals`.
- **Gut-check intent before rules** — "would the user, seeing this, find it makes sense? Rules resolve ties, not intent."
- **Self-audit against *named* failure modes** — pre-name the 1–3 costliest traps; "double-check" alone is too vague to change behavior.
- **Discrimination test for look-alike intents** — give an explicit "how to tell which they mean."
- **Calibrate effort to honest difficulty** — judge hardness first; brevity on easy cases is intelligence, not laziness.
- **Bias toward the cheaper-to-recover error** under uncertainty (e.g., a wrong draft beats a non-answer).
- **Infer the unsaid — with a restraint clause** so implication inference doesn't over-reach.
- **Pause on the downstream human** — include what's actionable, omit keys they can't use.

Full detail + reusable templates: `references/prompting-canon.md` §11.

## Prompt-Optimization Workflow (vendor-generic)

When asked to improve a prompt: **diagnose** intent + scope → **find gaps** (missing output contract, success criteria, scope boundaries, grounding rules, stop conditions) → **choose the control surface** → **draft minimal**, adding structure only where a gap or eval justifies it → **eval and iterate** one change at a time. Output a diagnosis, recommended settings, a full optimized prompt, a quick version, and a rationale table. Detail: `references/prompting-canon.md` §6.

## Temperature (corrected)

The old "0.0 for classification / 0.7 for chat" cookbook is misleading for current models. Reasoning models often ignore or disallow temperature; **Gemini 3 should stay at its default 1.0** (lowering it can cause loops/degradation). Control behavior with the reasoning/verbosity knobs instead. For creative variety, ask the model to "propose N options, then choose" rather than raising temperature. The legacy temperature intuition still applies only to classic non-reasoning completion models.

## Debugging Checklist

```
□ Over-prompting?    → strip legacy scaffolding; go outcome-first
□ Overthinking?      → lower effort; add stop criteria; "pick one approach and commit"
□ Under-thinking?    → raise effort/thinking knob (don't just add words)
□ Over-eager tools?  → tighten rules; "don't guess missing parameters"
□ Hallucinated?      → quote-then-answer; "investigate before answering"
□ Format drift?      → Structured Outputs; match prompt style to output; format at end
□ Prefill 400 error? → remove final-turn prefill (Claude 4.6+)
□ Inconsistent runs? → pin model+version; set effort; stricter output contract
```

## Anti-Patterns (prompt smells)

```
🚩 "Be helpful"/"be accurate" — specify HOW
🚩 Over-prompting a capable model with step-by-step process it doesn't need
🚩 "CRITICAL: You MUST ALWAYS…" intensity → over-triggering on newer models
🚩 Hand-written CoT when a thinking mode exists
🚩 Final-turn prefill on Claude 4.6+ (hard error)
🚩 Old temperature cookbook on reasoning models / Gemini 3
🚩 Most-important-docs-last in long context (now: data top, query end)
🚩 Negative-only instructions → give a positive target
🚩 Mixing XML + Markdown structure (esp. Gemini)
🚩 "Always/Never" with no escape hatch
🚩 Mechanical rule-following on ambiguous input → add a "be the user reading this" self-audit
🚩 "Double-check your work" with no named failure mode → name the specific trap
```

## Quick Technique Picker

| Task | Use |
|------|-----|
| Simple Q&A / common task | Zero-shot + clear constraints |
| Style/format mimicry | Few-shot (3–5 tagged examples) |
| Hard reasoning/math | Raise thinking/effort knob (not manual CoT) |
| Multi-step you must inspect | Prompt chaining (self-correction) |
| Factual accuracy | RAG + quote-then-answer + citations |
| Strict machine output | Structured Outputs / function calling |
| Long documents | Data at top, query at end, quote grounding |
| Tool use / agents | Calibrated tool rules + stop conditions + safety gates |
| Ambiguous / metaphorical request | Reframe + perspective-shift triggers (Natural Intelligence §11) |
| Need concise vs verbose | Verbosity param or explicit length target |

## Resources

- `references/prompting-canon.md` — full canon (control surface, agentic deep-dive, optimization workflow, dated model landscape)
- `references/quick-reference.md` — one-page cheat sheet
- `templates/prompt-templates.md` — ready-to-use templates
- `examples/before-after-examples.md` — improvement case studies (incl. 2026-era fixes)
- `scripts/prompt-validator.py` — automated quality checks

## Related Skills

- `prompt-optimizer` — analyze/rewrite a draft prompt and map it to ecosystem components
- `rag-implementation`, `function-calling`, `llm-evaluation` — when prompting alone isn't enough

---

**Remember:** the best prompts are **specific** about outcome and output, **minimal** (no scaffolding the model doesn't need), **tuned** at the control surface, **tested** on real examples, and **appropriate** to the task and the specific model.
