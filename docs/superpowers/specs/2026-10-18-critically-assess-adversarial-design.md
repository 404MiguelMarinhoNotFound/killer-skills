# critically-assess-adversarial: design spec

Date: 2026-10-18
Status: draft for review
Source: the critically-assess stress test (`critically-assess/docs/stress-test-2026-10-18.md`) and the brainstorm that followed it.

## 1. Why this exists

The 2026-10-18 stress test found that critically-assess does not beat a plain answer:

- The skill lost all 9 blind comparisons against one careful answer, at about 5× the cost.
- It reached the same verdict as the plain answer in 9 of 9 cases.
- The supervisor's sealed view matched the final verdict in 12 of 13 runs.
- 9 of 13 councils were unanimous. Copies of one model given the same brief converge, so the "opposing" roles did not oppose.

The value of a council lies in catching the cases where a first answer is wrong. The test set contained almost none of those, and the council was not built to look for them.

**Problem statement.** Build a decision skill that catches the mistakes a single careful answer makes and turns the result into a decision the user can act on. It must keep the honesty guarantees and must not reward either caving to criticism or defending the first answer by reflex.

## 2. Decisions already made

| Question | Decision |
|---|---|
| What counts as success | Catching wrong first answers. On cases where a careful first answer is wrong or badly framed, the skill reaches a better decision. Usefulness of the output matters but comes second. |
| Cost model | A full council on every run. No adaptive escalation. |
| Approach | An adversarial **hearing**: an independent thesis is attacked, defended once and judged. |
| Who holds the thesis | An independent first-pass agent. The supervisor acts only as the neutral judge and never writes the thesis. |
| Existing skill | `critically-assess` stays exactly as it is. The new skill is a copy with a new name. |

## 3. Scope

**In scope**
- A new skill folder, `critically-assess-adversarial/`, created by copying `critically-assess/` and then changing the copy.
- A new workflow, new roles, a new contract, script changes, report changes and tests.
- An evaluation harness and case set that measure catching, caving and the crux.

**Out of scope**
- Any change to `critically-assess/`: no edits to its files, tests or behaviour.
- Adaptive depth or a cheap mode.
- Proving who wrote a file. The ordering checks still rely on file times the supervisor controls, as in critically-assess.

## 4. Name and layout

The skill is named **critically-assess-adversarial**, and the frontmatter `name` matches the folder. The name marks it as the adversarial variant of critically-assess: a first answer gets a hearing, with a case, a challenge, a defence and a judgement. Because the two names are so close, the description must say plainly when to use this one (to challenge a first answer on a high-stakes decision) rather than critically-assess (a balanced pros-and-cons assessment). Otherwise the two skills will compete for the same requests. Trigger overlap between the two skills is checked in the evaluation (section 11).

```
critically-assess-adversarial/
  SKILL.md
  reference/contracts.md
  roles/            _attack_contract.md, thesis.md, reframer.md, rival.md,
                    premortem.md, outside-view.md, analyst.md, rebuttal.md
  scripts/          validate.py, assemble.py, render.py, role_library.py, scoring.py
  templates/report.html
  tests/
  eval/             cases/, key/, run_eval.py, score.py   (see section 10)
  docs/
```

These files start as copies of critically-assess and are then changed: `scoring.py`, `role_library.py`, the render plumbing and the test layout. The three critically-assess roles with no counterpart here (contrarian, executor and outsider) are not copied. First-principles and expansionist are not copied either: the reframer and the rival advocate replace them.

## 5. The flow

```
0 Prepare (supervisor)     research, brief.json, seal the brief
1 Thesis (1 agent)         thesis.reply.json, then the supervisor seals the thesis
2 Attacks (5 in parallel)  reframer, rival, premortem, outside-view, analyst
3 Rebuttal (1 agent)       the thesis author answers the strongest objections once
4 Judgement (supervisor)   classify each objection, apply the flip rule, write synthesis.json
5 Report                   assemble.py, then render.py
```

### 5.0 Prepare
- **Research:** the user chooses as in critically-assess (Online, Repo, Both or Neither). If the supervisor cannot ask, it treats the answer as Neither, records `research_asked: false` in the brief and puts "no research was done" in `unknowns` (enforced).
- **Brief:** written as in critically-assess, with two changes:
  - **The lean stays out.** A preference the user stated ("I'm leaning towards X") is kept out of the brief and stored in `user_lean.txt`. No agent reads that file. The judge addresses the lean in the verdict.
  - **Weights come from the user.** Each criterion records whether its weight was stated by the user or inferred by the supervisor (`"weight_source": "user" | "inferred"`). The report says when weights were inferred.
- **Seal:** `validate.py --seal-brief <run_dir>` writes `brief.sha256`.

### 5.1 Thesis
- One fresh agent reads the brief and its role file, nothing else, and writes `reports/thesis.reply.json`. Section 6 gives the shape.
- The supervisor runs `validate.py --seal-thesis <run_dir>`, which checks the thesis's shape and writes `thesis.sha256`. It refuses once any attack reply exists.
- If the thesis fails validation, the role is relaunched once with its errors appended. If it fails twice, **the run stops** and tells the user. The supervisor never writes the thesis.

### 5.2 Attacks
The five members launch in one message, all in parallel. Each reads its role file, `_attack_contract.md` (the analyst has its own contract), the brief and the thesis.

| Role | Job | Targets |
|---|---|---|
| reframer | Is the question or the option set wrong? It may propose one missing option with a short case for it. | frame |
| rival | Builds the strongest case and a plan for the thesis's runner-up, from that option's most favourable assumptions (dialectical inquiry). | thesis, rival |
| premortem | "It is a year later and this failed; why?" It runs once on the thesis and once on the runner-up. | thesis, rival |
| outside-view | Names a reference class and its typical outcome (base rate), and checks whether the thesis and the runner-up each assume they will beat it. | thesis, rival |
| analyst | Neutral 1–5 scores for every option on every criterion. This is an input to the judge, never the verdict. | all options |

**Rules for every attacker except the analyst:**
1. **Restate first.** `restatement` holds the thesis in the attacker's own words, faithfully enough that its author would agree with it (Rapoport's first rule).
2. **Number every objection.** Each one says what it targets, carries an evidence tag (`Brief:`, `Source:`, `Mechanism:` or `Knowledge:`, with the same checks as critically-assess) and gives its own `novelty` tag:
   - `new`: the thesis did not consider it;
   - `priced_in`: the thesis named it in `priced_in_risks`;
   - `meets:F<n>`: it claims a flip criterion holds.
3. **Failing is allowed.** `attack_result` is `landed` or `failed`. "My attack found nothing decisive" is a complete and valid answer, so no role has to invent doubt.

Access to the web and the repo follows `brief.research`, as in critically-assess. The thesis author and the analyst always work from the brief alone.

### 5.3 Rebuttal
- The thesis author answers once. Preferably the same agent is continued through SendMessage so it keeps its reasoning; otherwise a fresh agent gets the thesis and the attacks.
- It reads every attack reply and writes `reports/rebuttal.reply.json`, answering at most 5 objections. It chooses which, but must include every objection tagged `meets:F<n>`.
- For each objection it writes `concede` or `answer`, with a reason.
- It may not change the thesis. A concession is evidence for the judge, not an edit.

### 5.4 Judgement
The supervisor reads everything and writes `synthesis.json`.

- **Classify every objection.** `upheld_kind` is one of:
  - `meets_flip:F<n>`;
  - `new_decisive`: it changes the verdict, and the thesis would have listed it as a flip criterion had it known;
  - `new_minor`;
  - `priced_in`;
  - `role_filler`;
  - `refuted`: the rebuttal or the evidence defeats it.
- **The flip rule.** The final verdict differs from the thesis only through an objection classed `meets_flip` or `new_decisive`. The number of objections, and how many roles raised a point, never count.
- **Outcome:**
  - `survived`: same verdict, no change;
  - `amended`: same verdict, with a changed plan, conditions or crux;
  - `overturned`: a different verdict.
- **Evidence ranking** is as in critically-assess: `Source:` and `Brief:` first, then `Mechanism:`, then `Knowledge:`. A `Knowledge:` claim raised by several roles counts once. When a deciding objection rests on `Knowledge:` only, the judge checks it if the research setting allows. If it does not, the outcome may still change, but the claim goes into `unknowns` and the confidence drops.
- **The lean.** If `user_lean.txt` exists, the verdict summary answers it directly.

### 5.5 Report
The report leads with, in order:
1. the verdict and a short summary;
2. the plan: 3 to 6 concrete steps, with the user's own numbers worked out where the brief gives them;
3. **the crux to check first**: the fact that would most change the verdict, and the cheapest way to check it;
4. **the hearing outcome**: survived, amended or overturned; the deciding objection in one sentence; or, if it survived, the strongest objection that was not upheld;
5. confidence, with one sentence on why.

Behind a fold: the thesis, each attack, the rebuttal, the analyst's scores (marked "weights inferred" when they were), blind spots, unknowns and the audit trail. The report never calls an objection a "disagreement" when its `attack_result` was `failed`.

## 6. Contracts (shapes)

`reports/thesis.reply.json`
```json
{"role": "thesis",
 "verdict": "B",
 "summary": "...",
 "reasoning": ["..."],
 "plan": ["step 1", "step 2", "step 3"],
 "runner_up": "D",
 "priced_in_risks": ["..."],
 "flip_criteria": [{"id": "F1", "fact": "MkDocs core is in maintenance-only mode", "would_change_to": "E"}],
 "confidence": "medium"}
```
- In single mode, `verdict` is `go`, `no-go` or `conditional-go`, as in critically-assess, and `runner_up` is the other side.
- There are 1 to 3 flip criteria, each a checkable fact, not a feeling.

`reports/<attacker>.reply.json`
```json
{"role": "premortem",
 "restatement": "...",
 "objections": [{"id": "premortem-1", "target": "thesis", "claim": "...",
                 "evidence": "Mechanism: ...", "novelty": "new"}],
 "attack_result": "landed",
 "role_fields": {}}
```
Role-specific `role_fields`:
- **reframer:** `missing_option: {name, description, case} | null`
- **rival:** `case`, `plan`
- **outside-view:** `reference_class`, `base_rate`, `thesis_assumes_beating_it: bool`, `rival_assumes_beating_it: bool`
- **premortem:** `failure_stories: {thesis: [...], rival: [...]}`

`reports/analyst.reply.json`: unchanged from critically-assess (ledger and scores).

`reports/rebuttal.reply.json`
```json
{"role": "rebuttal",
 "responses": [{"objection": "premortem-1", "stance": "concede", "reason": "..."}]}
```

`synthesis.json` (judgement only; `assemble.py` copies in the brief, the thesis, the attacks, the rebuttal and the roster)
```json
{"title": "...",
 "classifications": [{"objection": "premortem-1", "upheld_kind": "new_decisive", "why": "..."}],
 "outcome": "overturned",
 "deciding": ["premortem-1"],
 "strongest_not_upheld": {"objection": "rival-2", "why": "..."},
 "verdict": {"decision": "...", "summary": "...", "conditions": []},
 "plan": ["..."],
 "crux": {"fact": "...", "how_to_check": "..."},
 "lean_answer": "...",
 "blind_spots": ["..."],
 "confidence": "medium",
 "confidence_why": "...",
 "unknowns": ["..."]}
```
- `strongest_not_upheld` may be null when every attack failed.
- `lean_answer` is required only when `user_lean.txt` exists.

## 7. Integrity checks (enforced by `validate.py`)

**Carried over from critically-assess:**
- the brief is sealed and must match `brief.sha256`;
- each reply file holds exactly one JSON object;
- replies are copied into `result.json` unchanged;
- `Source:` items must point at something the role could have opened under `brief.research`;
- a dropped reply must genuinely fail validation;
- every reply must come from a role on the roster;
- dropped roles must be named in `unknowns`;
- usage errors print a message instead of a traceback.

**New:**
1. **Order of events.** The brief seal comes before the thesis. The thesis seal (`thesis.sha256`) comes before every attack reply. Every attack reply comes before the rebuttal, and the rebuttal comes before `result.json`. Any violation is an error.
2. **The thesis is unchanged.** `thesis.reply.json` must match `thesis.sha256`. The roster's thesis entry may never use the model `supervisor`.
3. **Every attack restates.** `restatement` is a non-empty string, and every objection has an id that is unique across the run.
4. **The rebuttal covers flip claims.** Every objection tagged `meets:F<n>` appears in the rebuttal's `responses`, and every `F<n>` it names exists in the thesis.
5. **Every objection is classified.** Each objection id appears exactly once in `classifications`, and each `meets_flip:F<n>` names an existing criterion.
6. **Outcome matches verdict.**
   - A verdict that differs from the thesis verdict requires `overturned`.
   - `overturned` requires a different verdict.
   - `survived` requires the same verdict and no `deciding` entries.
7. **The flip rule.** `amended` and `overturned` need at least one `deciding` id, and each must be classed `meets_flip:*` or `new_decisive`. An objection classed `priced_in`, `role_filler`, `refuted` or `new_minor` may never decide.
8. **No quiet survival.** If any objection is classed `meets_flip:*`, the outcome cannot be `survived` unless that objection is the rebuttal's `answer` (not `concede`) and its classification `why` says why the answer holds. This is a warning when the rebuttal answered, and an error when it conceded.
9. **The plan and the crux.** `plan` has 3 to 6 non-empty steps, and `crux.fact` and `crux.how_to_check` are non-empty.
10. **Lean and research disclosures.** `lean_answer` is required when `user_lean.txt` exists. `unknowns` must say no research was done when `research_asked` is false.

**Warnings (they never fail the run):**
- A deciding objection rests only on `Knowledge:` evidence.
- The outcome is `overturned` to the analyst's lowest-scored option.
- Every attack reports `landed` while the outcome is `survived`, or every attack reports `failed` while the outcome is `overturned`.

## 8. Failure handling

- **Infrastructure failures are not attempts.** A launch refused by the tool, or a member killed by a rate limit or concurrency cap before it wrote its file, does not count. The supervisor waits and launches it again.
- **Thesis:** one relaunch with its errors appended. On a second failure the run stops.
- **Attackers:** one relaunch with errors appended. A second failure drops the role, as in critically-assess, and it must be named in `unknowns`. A hearing needs at least the rival and one of premortem or outside-view. Otherwise the run stops.
- **Analyst:** one relaunch. On a second failure the supervisor may write its scores tagged `Supervisor:`, as in critically-assess, and the report says so. The analyst is an input, not a party to the hearing.
- **Rebuttal:** one relaunch. On a second failure the hearing goes ahead without a rebuttal, and check 8 then treats every `meets_flip` objection as unanswered.

## 9. Cost

Each run uses 1 thesis + 5 attackers + 1 rebuttal = 7 agents in 3 waves, plus the supervisor. That is roughly 6–7× a plain answer, against about 5× for critically-assess. Wall time is about three times the slowest agent.

## 10. Evaluation

The evaluation lives in `critically-assess-adversarial/eval/` and runs as described in the brainstorm's section 3.

**Cases.** There are 12 cases, each with an answer key:
- **8 traps**, two of each type:
  - frame (the best option is not listed);
  - base rate (the plan assumes it will beat how similar efforts usually go);
  - hidden fact (one sentence in the brief decides the case);
  - values (the user's stated priority contradicts the obvious pick).
- **4 controls**, where the obvious first answer is right.

Each key gives the correct verdict and the crux: the planted deciding fact or missing option.

**Authorship and blindness.**
- Cases and keys are written by someone other than the supervisor under test: the user, or a separate agent.
- Keys live in `eval/key/`, which neither the supervisor nor any role reads.
- Scoring is done by `eval/score.py` against the key. No model judges the main metrics.

**Qualifying cases.** Before the main runs, each case is answered 3 times by a plain first-pass agent.
- A trap is kept only if the plain answer is wrong at least 2 of 3 times.
- A control is kept only if the plain answer is right 3 of 3 times.
- Anything else is rewritten or dropped.

**Conditions.** Each case runs 2 times under each condition:
1. **plain:** one agent answers.
2. **self-critique:** one agent answers, critiques its own answer, then revises.
3. **hearing:** critically-assess-adversarial (the skill under test).

**Metrics.**
- **Catch rate:** on traps, the share of final verdicts that match the key.
- **Cave rate:** on controls, the share of runs where the hearing turned a correct thesis into a wrong verdict.
- **Crux hit:** on traps, whether `crux.fact` names the key's crux. A short script lists the pair, and a human or a blind judge confirms the match.
- **Supporting signals:** the survived / amended / overturned mix; the `upheld_kind` of deciding objections; cost and wall time; a blind usefulness comparison against plain (secondary).

**Pass bar, fixed before any run.**
- **Catches:** the hearing catches at least 4 more trap runs than self-critique, out of 16, and more than plain.
- **Caves:** at most 1 cave across the 8 control runs.
- **Crux hits:** in more than half of the hearing's catches.

If the hearing does not beat self-critique, the extra agents are not earning their cost, and the report says so.

**Pilot first.** A pilot of 3 traps (frame, base rate, hidden fact) and 1 control, run once each, comes before the full set. It also spaces launches to stay under the 20-subagent concurrency cap.

## 11. Testing (pytest)

- Every check in section 7 gets at least one passing and one failing test. Tests build a sample hearing run, like `tests/sample_run.py`.
- Tamper tests, ported from the stress test's script:
  - the thesis edited after its seal;
  - an attack written before the thesis seal;
  - the rebuttal written before an attack;
  - a deciding objection classed `priced_in`;
  - an `overturned` outcome with an unchanged verdict;
  - `survived` despite a conceded flip objection;
  - a supervisor-written thesis;
  - a missing `lean_answer`;
  - a valid attack dropped.
- `test_skill_md.py` and `test_role_library.py` are ported, and the no-verbatim test is kept.
- A trigger-overlap check: a small fixture of prompts, with an agent asked which of the two descriptions applies. This runs as a documented eval step, not in pytest.
- `critically-assess/tests` must still pass unchanged after the copy, as proof that the original was not touched.

## 12. Resolved questions

1. **Rebuttal mechanics.** The supervisor continues the thesis agent through SendMessage, so the author keeps its own reasoning. If SendMessage is unavailable or the agent cannot be resumed, a fresh agent gets the thesis and all attacks instead. The roster records which path was used (`"rebuttal_mode": "continued" | "fresh"`).
2. **The reframer's missing option.** There is no second wave. The reframer argues for its own missing option in `role_fields.missing_option.case`, and the judge may class that objection `new_decisive`. A second rival wave is deferred until the evaluation shows frame traps being missed.
3. **Model diversity.** The role library defaults put the thesis author and the analyst on `opus`, and the rival and premortem on `sonnet`, so the strongest attacks come from a different model than the thesis. The reframer and outside-view use `opus`. Each default can be overridden per run, as in critically-assess.
4. **Case authorship.** A separate agent, which never acts as supervisor in the evaluation, drafts the 12 cases and their keys. The user reviews and approves each key before the cases are qualified. Keys stay in `eval/key/`.
