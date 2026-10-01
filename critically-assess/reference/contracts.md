# Contracts

Every file lives in the run directory `.critically-assess/runs/<YYYYMMDD-HHMMSS>-<slug>/` under the user's working directory.

## brief.json (step 3)

```json
{
  "mode": "multi",
  "question": "The decision in one neutral sentence",
  "options": [
    {"id": "A", "name": "Short name", "description": "What this option means concretely"},
    {"id": "B", "name": "Short name", "description": "..."}
  ],
  "context": "What the council needs to know about the situation",
  "evidence": [{"claim": "A fact you will rely on", "source": "URL, file path, 'user' or 'general knowledge (unverified)'"}],
  "constraints": ["Hard limits: time, budget, team, tech"],
  "stakes": "Why a wrong call is costly, and how hard it is to reverse",
  "research": "both",
  "criteria": [
    {"id": "fit", "name": "Readable name", "weight": 0.4, "why": "Why it deserves this weight for this user"}
  ]
}
```

- Single mode: exactly two options. `A` is the idea; `B` is `{"id": "B", "name": "Status quo", "description": "Keep doing what happens today"}`.
- Use 3 to 6 criteria. A weight is any positive number; the scripts normalize them.
- Keep it neutral. No adjectives that favour an option, no hint of your own view.
- `research` records the user's answer in step 2 (`online`, `repo`, `both` or `none`). It sets what council voices may look up; the analyst always works from the brief alone.

## precommit.json (step 4, sealed until step 7)

Written first to `${TMPDIR:-/tmp}/critically-assess-sealed/<run-id>.json`, outside the working directory, and moved into the run folder only after every council reply is saved.

```json
{"position": "Your view before the council", "reasons": ["first", "second", "third"], "main_risk": "The biggest risk in your own view"}
```

## reports/<role>.raw.txt (step 7)

The subagent's reply, saved verbatim. The file name is the role id; `validate.py` overwrites the `role` field with it. Every council `evidence` item must start with `Brief:`, `Source:`, `Mechanism:` or `Knowledge:`; analyst ledger evidence with `Brief:`, `Mechanism:`, `Knowledge:` or `Supervisor:`. `scripts/validate.py` turns it into `reports/<role>.json`. Council roles follow `roles/_contract.md`, which includes `pick` (the option id the role favours) and `point` (its position in one line); the analyst follows its own contract in `roles/analyst.md`.

## result.json (step 8)

```json
{
  "title": "Short title for the report",
  "brief": {"...": "the full brief.json"},
  "precommit": {"...": "the full precommit.json"},
  "roster": [{"role": "contrarian", "model": "opus", "why": "One line on why this role is on this council"}],
  "reports": ["...every council role report object, analyst excluded"],
  "analyst": {"...": "the analyst report object"},
  "ledger": [
    {"option": "A", "kind": "pro", "point": "One short line", "claim": "...", "severity": 4, "likelihood": 3, "raised_by": ["analyst", "executor"]}
  ],
  "scores": [{"option": "A", "criterion": "fit", "score": 4, "rationale": "..."}],
  "dissent": {"role": "expansionist", "position": "The strongest view you did not adopt", "why_rejected": "..."},
  "blind_spots": ["Something no voice raised"],
  "drift": "How and why the verdict moved from precommit.json, or 'None' plus the reason",
  "verdict": {"decision": "A", "summary": "The decision and its main reason, explained in plain words", "conditions": []},
  "first_step": "One concrete action",
  "confidence": "medium",
  "unknowns": ["What would change the verdict if it turned out differently"]
}
```

- `verdict.decision`: in single mode `go`, `no-go` or `conditional-go` (the last one requires `conditions`); in multi mode an option id or `hybrid`.
- `ledger`: merge the analyst's ledger with the council's pros and cons. Collapse duplicates into one item and list every role that raised it in `raised_by`. Drop anything without evidence. Give every item a `point`: the claim in one short line, which the report lists under that option's name, so the point may leave the name out. The full `claim` opens beneath it.
- `scores`: start from the analyst's. If you change one, prefix its rationale with `Supervisor:` and say why.
- Every sentence the reader sees follows "Write for the reader" in SKILL.md step 8. That is judged in the coherence pass, not by a script; `validate.py` checks structure only.
- `roster`: 3 to 5 council roles plus the analyst, leaving out any role dropped into `reports/dropped/`. Write `inherited` as the model if the subagent tool refused the model parameter, or `supervisor` for an analyst report you had to write yourself.
- `validate.py` checks every field the report reads: the full option × criterion grid in `scores` (integers 1-5, known ids only), `raised_by` as a list of role ids, a `point` on every ledger item, each council report's `pick` as a known option id, and `dissent`, `verdict.summary`, `first_step` and `drift` as non-empty strings. `render.py` refuses to render a `result.json` that fails validation.
