# critically-assess-adversarial Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `critically-assess-adversarial/`, a copy of `critically-assess/` reworked into an adversarial hearing. An independent thesis is attacked by five roles, rebutted once and judged under a flip rule. An evaluation harness then measures whether it catches wrong first answers without caving on right ones.

**Architecture:** The skill is a folder of Markdown instructions (`SKILL.md`, `roles/`, `reference/`), standard-library Python scripts and one HTML template. Validation is split in two:
- `scripts/contracts.py` holds pure shape validators for each reply (thesis, attack, rebuttal).
- `scripts/validate.py` holds run-level checks: seals, order of events, roster, the judgement and the CLI.

`assemble.py` builds `result.json` from the supervisor's `synthesis.json` and the run files. `render.py` produces the report. `eval/score.py` scores evaluation runs against answer keys.

**Tech Stack:** Python 3.10+ standard library only, pytest, one self-contained HTML/JS template.

**Spec:** `docs/superpowers/specs/2026-10-18-critically-assess-adversarial-design.md`. Section numbers below (§) refer to it.

## Global Constraints

- `critically-assess/` must not change. Run `git diff --quiet HEAD -- critically-assess` before every commit, and expect exit 0.
- The skill folder and the frontmatter `name` are both `critically-assess-adversarial`.
- Scripts need Python 3.10+ and nothing outside the standard library.
- `brief.research` is one of `online`, `repo`, `both`, `none`. The brief gains `research_asked` (bool, default true). Each criterion gains `weight_source`: `"user"` or `"inferred"`.
- Roles and default models:
  - `thesis` opus, `reframer` opus, `rival` sonnet, `premortem` sonnet, `outside-view` opus, `analyst` opus, `rebuttal` opus.
  - Attackers are `reframer`, `rival`, `premortem`, `outside-view`.
  - The analyst follows its own contract.
- Thesis rules:
  - 1 to 3 flip criteria with ids `F1`..`F3`.
  - `runner_up` is an option id different from the verdict's backed option.
  - In single mode the verdict is one of `go`, `no-go`, `conditional-go`.
- Objection `novelty` is `new`, `priced_in` or `meets:F<n>`. `attack_result` is `landed` or `failed`.
- The rebuttal has at most 5 responses, each with `stance` `concede` or `answer`, and must cover every `meets:` objection.
- Judge classes (`upheld_kind`): `meets_flip:F<n>`, `new_decisive`, `new_minor`, `priced_in`, `role_filler`, `refuted`.
- `outcome` is one of `survived`, `amended`, `overturned`.
- The synthesis `plan` has 3 to 6 steps. `crux` has `fact` and `how_to_check`.
- The roster records `"rebuttal_mode": "continued" | "fresh"` on the rebuttal entry.
- A hearing needs `thesis`, `rival`, and at least one of `premortem` or `outside-view`. The thesis can never have model `supervisor` and can never be dropped.

## Review Focus

1. **Single mode: `go` → `conditional-go` must not count as overturning.** Outcome comparison uses the backed option (`go` and `conditional-go` back A, `no-go` backs B). Same backed option with different conditions is `amended`. Pinned in Task 5.
2. **The final verdict can be the reframer's missing option.** In multi mode `verdict.decision` may be `"missing-option"`, but only when the reframer reply has a non-null `missing_option` and `deciding` includes a reframer objection. In single mode the decision is `no-go`, and a warning fires if the summary does not name the missing option. Pinned in Task 5.
3. **Objection ids that collide, or references to ids that do not exist,** from the rebuttal, `classifications` or `deciding`, each name the bad id in an error. Pinned in Tasks 2 and 5.
4. **A run with no rebuttal** (dropped after two failures) assembles with `"rebuttal": null`. Check 8 then treats every `meets_flip` objection as unanswered. Pinned in Task 5.
5. **A hearing where every attack failed** is valid: `outcome` `survived`, `strongest_not_upheld` null, no `deciding`. Pinned in Task 5.

---

### Task 1: Copy the skill and rename it

**Files:**
- Create: `critically-assess-adversarial/` (a copy of `critically-assess/`, excluding `docs/stress-test-2026-10-18.md`, `tests/__pycache__` and any `.critically-assess/` folder)
- Modify: `critically-assess-adversarial/SKILL.md` (frontmatter `name` only, for now)
- Modify: `critically-assess-adversarial/tests/test_skill_md.py` (`test_frontmatter`)
- Modify: `critically-assess-adversarial/tests/conftest.py` (environment variable name)
- Modify: `critically-assess-adversarial/scripts/render.py` (environment variable name)

**Interfaces:**
- Produces: a copied skill whose tests pass, plus the environment variable `CRITICALLY_ASSESS_ADVERSARIAL_NO_OPEN`, used by `render.open_in_browser` and the conftest fixture.

- [ ] **Step 1: Copy.** Run `cp -r critically-assess critically-assess-adversarial`, then `rm -rf critically-assess-adversarial/tests/__pycache__ critically-assess-adversarial/docs/stress-test-2026-10-18.md`.
- [ ] **Step 2: Change the test first.** In the copy's `test_frontmatter`, assert `meta["name"] == "critically-assess-adversarial"`.
- [ ] **Step 3: Run it.** `cd critically-assess-adversarial && python -m pytest -q tests/test_skill_md.py`. Expected: FAIL on the name.
- [ ] **Step 4: Rename.** Set the frontmatter `name: critically-assess-adversarial` in the copy's `SKILL.md`. Rename the environment variable `CRITICALLY_ASSESS_NO_OPEN` to `CRITICALLY_ASSESS_ADVERSARIAL_NO_OPEN` in the copy's `render.py` and `conftest.py`.
- [ ] **Step 5: Run both suites.** Run `python -m pytest -q` in each folder. Expected: copy 141 passed, 1 skipped; original 141 passed, 1 skipped. Then run `git diff --quiet HEAD -- critically-assess` and expect exit 0.
- [ ] **Step 6: Commit.** `git add critically-assess-adversarial && git commit -m "critically-assess-adversarial: start as a copy of critically-assess"`

### Task 2: Reply contracts (`scripts/contracts.py`)

**Files:**
- Create: `critically-assess-adversarial/scripts/contracts.py`
- Create: `critically-assess-adversarial/tests/test_contracts.py`

**Interfaces:**
- Consumes, from `validate.py` (unchanged at this point): `_is_text`, `_is_text_list`, `_dicts`, `COUNCIL_TAGS`, `SINGLE_DECISIONS`, `CONFIDENCE`, `_decided_option(mode, decision)`.
- Produces:
  - `ATTACKERS = ("reframer", "rival", "premortem", "outside-view")`
  - `UPHELD_KINDS = ("new_decisive", "new_minor", "priced_in", "role_filler", "refuted")`. A `meets_flip:F<n>` class is matched by `FLIP_KIND = re.compile(r"^meets_flip:(F[1-3])$")`.
  - `NOVELTY = re.compile(r"^(new|priced_in|meets:F[1-3])$")`
  - `validate_thesis(thesis: dict, brief: dict) -> list[str]`
  - `validate_attack(reply: dict, brief: dict, thesis: dict) -> list[str]`
  - `objection_index(attacks: list[dict]) -> tuple[dict[str, dict], list[str]]`. Maps objection id to the objection plus `"_role"`, and returns errors for duplicate ids.
  - `validate_rebuttal(rebuttal: dict, objections: dict[str, dict], thesis: dict) -> list[str]`
  - `backed_option(mode: str, decision: str) -> str | None`. `go` and `conditional-go` give `"A"`, `no-go` gives `"B"`; in multi mode an option id maps to itself and `"missing-option"` maps to `"missing-option"`.

Every error string starts with the role it belongs to (`thesis:`, `premortem:`, `rebuttal:`).

- [ ] **Step 1: Write the failing tests** in `tests/test_contracts.py`, using small dicts built inline from `sample_run.BRIEF` (multi mode, options A Postgres and B DynamoDB):
  - `test_valid_thesis_passes`: thesis `{"role": "thesis", "verdict": "A", "summary": "s", "reasoning": ["r"], "plan": ["1", "2", "3"], "runner_up": "B", "priced_in_risks": ["k"], "flip_criteria": [{"id": "F1", "fact": "f", "would_change_to": "B"}], "confidence": "medium"}`. Assert `validate_thesis(...) == []`.
  - `test_thesis_rejects_bad_flip_criteria`: zero criteria, four criteria, id `F9`, and an empty `fact` each produce an error containing `flip_criteria`.
  - `test_thesis_runner_up_must_be_another_option`: `runner_up` equal to the verdict, and `runner_up` `"Z"`, each produce an error containing `runner_up`.
  - `test_single_mode_thesis_uses_go_no_go`: in single mode, verdict `"A"` is an error and `"conditional-go"` passes, with `runner_up` `"B"`.
  - `test_attack_needs_restatement_numbered_objections_and_result`: an attack missing `restatement`, with novelty `"maybe"`, and with `attack_result` `"won"` produces three errors naming those fields.
  - `test_attack_meets_must_name_a_real_flip_criterion`: novelty `meets:F2` when the thesis only has F1 gives an error containing `F2`.
  - `test_attack_role_fields_are_checked`: a rival without `role_fields.case`, and an outside-view whose `thesis_assumes_beating_it` is not a bool, each give an error. A reframer with `missing_option: null` passes.
  - `test_objection_ids_must_be_unique_across_the_run` (Review Focus 3): two attacks both using `premortem-1` make `objection_index` return an error containing `premortem-1`.
  - `test_rebuttal_must_answer_every_flip_claim_and_stay_short`: a missing `meets:` objection, 6 responses, stance `"maybe"`, and an unknown objection id `ghost-1` each produce an error naming the problem.
  - `test_backed_option`: `backed_option("single", "conditional-go") == "A"`, `backed_option("single", "no-go") == "B"`, `backed_option("multi", "B") == "B"`, `backed_option("multi", "missing-option") == "missing-option"`.
- [ ] **Step 2: Run them.** `python -m pytest -q tests/test_contracts.py`. Expected: FAIL with `ModuleNotFoundError: contracts`.
- [ ] **Step 3: Implement `scripts/contracts.py`** with the signatures above, mirroring the style of `validate_role_report`: never raise, collect error strings.
  - Evidence on each objection must start with one of `COUNCIL_TAGS`.
  - The `role_fields` required by role:
    - `reframer`: `missing_option`, null or `{name, description, case}`, all text;
    - `rival`: `case` (text) and `plan` (non-empty text list);
    - `premortem`: `failure_stories` with `thesis` and `rival` text lists;
    - `outside-view`: `reference_class` and `base_rate` (text), `thesis_assumes_beating_it` and `rival_assumes_beating_it` (bool).
- [ ] **Step 4: Run them.** Expected: PASS. Then run the full `python -m pytest -q`, expected still green.
- [ ] **Step 5: Commit.** `git add critically-assess-adversarial/scripts/contracts.py critically-assess-adversarial/tests/test_contracts.py && git commit -m "critically-assess-adversarial: reply contracts for thesis, attacks and rebuttal"`

### Task 3: Role library (the new roles replace the old)

**Files:**
- Delete: `roles/contrarian.md`, `roles/executor.md`, `roles/expansionist.md`, `roles/first-principles.md`, `roles/outsider.md`, `roles/_contract.md`
- Create: `roles/thesis.md`, `roles/reframer.md`, `roles/rival.md`, `roles/premortem.md`, `roles/outside-view.md`, `roles/rebuttal.md`, `roles/_attack_contract.md`
- Modify: `roles/analyst.md` (only one paragraph: it now scores options that a thesis exists for, and it still works from the brief alone and recommends nothing)
- Modify: `tests/test_role_library.py`
- Modify: `scripts/role_library.py`: `REQUIRED_KEYS` gains `wave`, valued `thesis`, `attack` or `rebuttal`; `check_roles` errors on any other value.

All paths are under `critically-assess-adversarial/`.

**Interfaces:**
- Consumes: the field names in Task 2's contracts. Role files must name them exactly: `restatement`, `objections`, `novelty`, `attack_result`, `role_fields`, `flip_criteria`, `priced_in_risks`, `runner_up`, `responses`, `stance`.
- Produces: `role_library.load_roles(dir)` returns 7 roles, each with a `wave` key. `role_library.by_wave(roles) -> dict[str, list[str]]` returns role ids grouped by wave.

- [ ] **Step 1: Write the failing tests.**
  - `test_library_has_the_hearing_roles`: ids == `{"thesis", "reframer", "rival", "premortem", "outside-view", "analyst", "rebuttal"}`.
  - `test_default_models`: `thesis` opus, `reframer` opus, `rival` sonnet, `premortem` sonnet, `outside-view` opus, `analyst` opus, `rebuttal` opus.
  - `test_waves`: `by_wave(...)` == `{"thesis": ["thesis"], "attack": ["analyst", "outside-view", "premortem", "reframer", "rival"], "rebuttal": ["rebuttal"]}`, lists sorted.
  - `test_attack_contract_names_every_field`: `_attack_contract.md` contains each of `restatement`, `objections`, `novelty`, `meets:F`, `priced_in`, `attack_result`, `failed`.
  - `test_thesis_role_asks_for_checkable_flip_criteria`: `thesis.md` contains `flip_criteria`, `runner_up` and `priced_in_risks`.
  - `test_rebuttal_role_cannot_change_the_thesis`: `rebuttal.md` contains `concede` and `answer`, and states that it does not change the thesis.
  - Keep `test_all_roles_pass_checks`, `test_underscore_files_are_not_roles` and `test_check_roles_catches_bad_model_and_unknown_tension`. The tmp role in that last test gains `wave: attack`.
- [ ] **Step 2: Run them.** Expected: FAIL (old ids, no `wave`).
- [ ] **Step 3: Write the role files.** Use the same frontmatter keys as today plus `wave`, and the sections `## Lens`, `## You must`, `## You must not`. Content per role comes from spec §5.1–5.3:
  - `thesis` answers from the brief alone, with 1 to 3 checkable flip criteria.
  - `reframer` may propose one missing option and argue its case.
  - `rival` uses the thesis's runner-up and that option's most favourable assumptions.
  - `premortem` runs once on the thesis and once on the runner-up.
  - `outside-view` names a reference class and base rate for both.
  - `rebuttal` answers at most 5 objections, including every `meets:` claim, and concedes when it should.

  `_attack_contract.md` holds the JSON shape from §6 and the three rules: restate first, number and tag objections, and failing is allowed. It also carries over critically-assess's "Looking things up" and "Writing so the reader understands" sections, adjusted to these field names.
- [ ] **Step 4: Implement `by_wave`** and the `wave` check in `role_library.py`. Run `python scripts/role_library.py`: expected exit 0 and 7 roles listed.
- [ ] **Step 5: Run the role tests.** Expected: PASS. Other suites may fail now because `sample_run` still uses the old roles; Task 4 replaces it.
- [ ] **Step 6: Commit.** `git add -A critically-assess-adversarial/roles critically-assess-adversarial/scripts/role_library.py critically-assess-adversarial/tests/test_role_library.py && git commit -m "critically-assess-adversarial: hearing roles replace the lens roles"`

### Task 4: Sample hearing run and brief changes

**Files:**
- Rewrite: `tests/sample_run.py`
- Modify: `scripts/validate.py` (`validate_brief` only)
- Modify: `tests/test_validate.py`: delete every test of the removed lens-council behaviour (precommit, unseal, patch, pick and point, dissent, ledger and roster tests written for the old roles). Keep the brief, source, `read_reply` and corrupt-file tests, adapted to the new sample.

**Interfaces:**
- Produces, in `sample_run`:
  - `BRIEF`: multi mode, options A Postgres and B DynamoDB, criteria `fit` (0.6) and `ops` (0.4) each with `"weight_source": "user"`, `"research": "both"`, `"research_asked": true`.
  - `THESIS`: verdict A, runner-up B, flip criterion `F1` = `{"id": "F1", "fact": "Finance stops needing ad-hoc joins", "would_change_to": "B"}`.
  - `ATTACKS`: a dict mapping each attacker role to a reply. Each has one objection, with ids `reframer-1`, `rival-1`, `premortem-1`, `outside-view-1`. `rival-1` has novelty `meets:F1`; the rest are `new` or `priced_in`. `reframer`'s `missing_option` is null.
  - `ANALYST`: the current one.
  - `REBUTTAL`: answers `rival-1` with stance `answer`.
  - `ROSTER`: all 7 roles. The rebuttal entry has `"rebuttal_mode": "continued"`.
  - `SYNTHESIS`: outcome `survived`, every objection classified, `rival-1` classed `refuted`, `plan` with 3 steps, `crux`, `strongest_not_upheld` naming `rival-1`.
  - `write_run(path) -> Path`. Writes `brief.json`, `brief.sha256`, `roster.json`, `reports/thesis.reply.json`, `thesis.sha256`, `reports/<attacker>.reply.json`, `reports/analyst.reply.json`, `reports/rebuttal.reply.json`, `synthesis.json` and `result.json`. Stamps each step's mtime 1 second apart with `os.utime`, in the §7 check-1 order.
  - `write_open_run(path) -> Path`. Same as `write_run`, but stops before the rebuttal, synthesis and result.
- Produces, in `validate.py`: `validate_brief` accepts and checks `research_asked` (a bool when present) and each criterion's `weight_source` (`"user"` or `"inferred"` when present).

- [ ] **Step 1: Write the failing tests** in `test_validate.py`:
  - `test_brief_research_asked_must_be_bool`
  - `test_criterion_weight_source_is_user_or_inferred`
  - `test_sample_parts_are_valid`: `contracts.validate_thesis(THESIS, BRIEF) == []`, and every attack passes `validate_attack`.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement** the `validate_brief` additions and rewrite `sample_run.py`. The order of writes and mtimes is the algorithm that matters: brief.sha256 < thesis.reply < thesis.sha256 < each attack and the analyst < rebuttal < synthesis < result.
- [ ] **Step 4: Run them.** Run `python -m pytest -q tests/test_validate.py tests/test_contracts.py`. Expected: PASS.
- [ ] **Step 5: Commit.** `git add -A critically-assess-adversarial/tests critically-assess-adversarial/scripts/validate.py && git commit -m "critically-assess-adversarial: hearing sample run and brief fields"`

### Task 5: Run-level validation (seals, order, roster and judgement)

**Files:**
- Modify: `scripts/validate.py`
- Create: `tests/test_hearing.py`

**Interfaces:**
- Consumes: everything Task 2 produces in `contracts`, plus `sample_run.write_run` and `write_open_run`.
- Produces, in `validate.py`:
  - `RESULT_KEYS = ("title", "brief", "roster", "thesis", "attacks", "analyst", "rebuttal", "scores", "classifications", "outcome", "deciding", "strongest_not_upheld", "verdict", "plan", "crux", "lean_answer", "blind_spots", "confidence", "confidence_why", "unknowns")`. `lean_answer` is optional.
  - `seal_brief(run_dir) -> list[str]`: writes `brief.sha256`; refuses once `reports/thesis.reply.json` exists.
  - `seal_thesis(run_dir) -> list[str]`: requires `brief.sha256`; validates the thesis with `contracts.validate_thesis`; writes `thesis.sha256`; refuses once any attacker or analyst reply exists.
  - `check_order(run: Path) -> list[str]`: implements §7 check 1 using mtimes.
  - `validate_roster_file(run) -> list[str]`: library roles only, each once; `thesis`, `rival` and `analyst` required; at least one of `premortem` or `outside-view` remains after drops; `thesis` never model `supervisor` and never dropped; `rebuttal_mode` in (`continued`, `fresh`) when present; every reply file belongs to a roster role.
  - `validate_judgement(result: dict) -> list[str]`: §7 checks 5–9 and Review Focus 1, 2, 4 and 5. It also keeps critically-assess's analyst checks (`validate_analyst_report`, `_check_analyst_authorship`, the full score grid, `Supervisor:` on changed scores, and the `unknowns` note for a supervisor-written analyst), because §8 still lets the supervisor write the analyst after two failures.
  - `check_disclosures(run: Path, result: dict) -> list[str]`: §7 check 10 (`user_lean.txt` requires `lean_answer`; `research_asked: false` requires an unknowns line containing "no research").
  - `judgement_warnings(result: dict) -> list[str]`: the three §7 warnings, plus Review Focus 2's single-mode missing-option summary warning.
  - `validate_run(run_dir, warnings=None) -> list[str]`: reads every `reports/*.reply.json` into a checked copy `reports/<role>.json` (as today); runs the reply contracts, `check_sources` on each attack's objection evidence, `check_dropped` (now using `validate_attack` for dropped attackers and refusing a dropped thesis), roster, order and seals. When `result.json` exists it also runs `validate_judgement`, `check_disclosures`, the copied-unchanged check and the warnings.
  - CLI: `validate.py <run_dir>`, `validate.py --seal-brief <run_dir>`, `validate.py --seal-thesis <run_dir>`.
- Removes: `seal`, `unseal`, `check_precommit`, `validate_precommit`, `apply_patch`, `_pick_warnings`, `validate_role_report`, the old `result_warnings`, and `--seal`/`--unseal`.

- [ ] **Step 1: Write the failing tests** in `tests/test_hearing.py`. Each starts from `run_dir` (from `write_run`) or `write_open_run` and changes one thing:
  - `test_sample_hearing_is_valid`: `validate_run(run_dir) == []`.
  - `test_seal_thesis_refuses_once_an_attack_exists` and `test_seal_brief_refuses_once_the_thesis_exists`.
  - `test_thesis_edited_after_seal_is_rejected`: the error contains `thesis.reply.json differs`.
  - `test_attack_written_before_the_thesis_seal_is_rejected` and `test_rebuttal_written_before_an_attack_is_rejected`: use `os.utime`; errors name both files.
  - `test_supervisor_cannot_write_or_drop_the_thesis`: roster thesis model `supervisor`, or a dropped thesis, each errors.
  - `test_hearing_needs_rival_and_one_of_premortem_or_outside_view`.
  - `test_every_objection_is_classified_exactly_once`: a missing id, a duplicate and `ghost-1` each errors (Review Focus 3).
  - `test_changed_verdict_requires_overturned` and `test_overturned_requires_changed_verdict`.
  - `test_go_to_conditional_go_is_amended_not_overturned` (Review Focus 1): in a single-mode sample, thesis `go`, final `conditional-go`, outcome `amended`, deciding a `new_decisive` objection: valid. Outcome `overturned` with the same pair: error.
  - `test_only_flip_or_new_decisive_objections_can_decide`: deciding `premortem-1` classed `priced_in` gives an error containing `cannot decide`.
  - `test_survived_needs_no_deciding_objections`.
  - `test_no_quiet_survival_after_a_concession`: rebuttal stance `concede` on `rival-1`, the judge classes it `meets_flip:F1`, outcome `survived`: error. Stance `answer` with a classification `why`: a warning, not an error.
  - `test_missing_rebuttal_treats_flip_claims_as_unanswered` (Review Focus 4): delete the rebuttal reply, drop the role into `reports/dropped/` with an invalid reply, set result `rebuttal` to null, classify `rival-1` as `meets_flip:F1`, outcome `survived`: error.
  - `test_all_attacks_failed_can_survive_without_a_strongest_objection` (Review Focus 5): every `attack_result` `failed`, `strongest_not_upheld` null, outcome `survived`: valid.
  - `test_missing_option_verdict_needs_a_reframer_objection` (Review Focus 2): decision `missing-option` with no reframer `missing_option`: error. With one, and `deciding` `["reframer-1"]` classed `new_decisive`: valid.
  - `test_plan_and_crux_are_required`: a 2-step plan and an empty `crux.how_to_check` each errors.
  - `test_lean_needs_an_answer` and `test_unasked_research_must_be_disclosed`.
  - `test_valid_attack_cannot_be_dropped`: carried over from the critically-assess test of the same idea.
  - `test_cli_prints_usage_for_bad_arguments`.
- [ ] **Step 2: Run them.** `python -m pytest -q tests/test_hearing.py`. Expected: FAIL.
- [ ] **Step 3: Implement** the interfaces above in `validate.py`. Reuse `_read`, `_safe`, `sha256_of`, `check_sources`, `working_dir_of` and `_role_names`. For check 7, the deciding objection's class must match `contracts.FLIP_KIND` or equal `new_decisive`. Compare outcomes with `contracts.backed_option` on the thesis verdict and the final verdict.
- [ ] **Step 4: Run them.** Run `python -m pytest -q`. Expected: PASS, except `test_assemble.py` and `test_render.py`, which still test the old shapes; Tasks 6 and 7 replace them.
- [ ] **Step 5: Commit.** `git add -A critically-assess-adversarial/scripts/validate.py critically-assess-adversarial/tests && git commit -m "critically-assess-adversarial: seals, order of events and the judgement checks"`

### Task 6: Assemble the result

**Files:**
- Modify: `scripts/assemble.py`
- Rewrite: `tests/test_assemble.py`

**Interfaces:**
- Consumes: `validate.RESULT_KEYS`, `validate.validate_run`, `validate._read`, and `validate._dropped`.
- Produces: `assemble(run_dir, synthesis_file) -> list[str]`, with `COPIED = ("brief", "roster", "thesis", "attacks", "analyst", "rebuttal")`.
  - `attacks` is the list of checked attacker reports in roster order, minus dropped roles.
  - `rebuttal` is null when the rebuttal role was dropped.
  - `scores` defaults to the analyst's.

- [ ] **Step 1: Write the failing tests.**
  - `test_assemble_copies_the_run_and_validates`: `write_open_run`, then the sample rebuttal and synthesis, then `assemble(...) == []`, and `validate_run == []`.
  - `test_synthesis_may_not_carry_copied_parts`: a synthesis containing `thesis` gives an error containing `leave`.
  - `test_assemble_with_a_dropped_rebuttal_writes_null`.
  - `test_assemble_cli_prints_ok`.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement** the changes to `COPIED`, the judgement keys and the copying. Keep the existing "the synthesis may not contain copied keys" and "unknown keys" errors.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "critically-assess-adversarial: assemble the hearing result"`

### Task 7: Report: terminal summary and HTML

**Files:**
- Modify: `scripts/render.py`
- Modify: `templates/report.html`
- Rewrite: `tests/test_render.py`

**Interfaces:**
- Consumes: the `result.json` shape from Task 6.
- Produces: `terminal_summary(result) -> str`. Its lines, in order:
  - `## <title>`
  - `Verdict: <name or decision> — <summary>`, then any conditions
  - `Hearing: <outcome>`, followed by ` by <role> (<objection claim>)` when deciding is non-empty
  - `Plan:`, then the numbered steps
  - `Crux to check first: <fact> (<how_to_check>)`
  - `Confidence: <level> — <confidence_why>`

  `main(run_dir, open_report=True)` is unchanged in behaviour. The template renders the same five items first, and everything else (the thesis, each attack, the rebuttal, analyst scores marked "weights inferred" when any criterion's `weight_source` is `inferred`, blind spots, unknowns) inside `<details>`.

- [ ] **Step 1: Write the failing tests.**
  - `test_terminal_summary_leads_with_verdict_plan_and_crux`: assert the line order above on the sample.
  - `test_overturned_names_the_deciding_objection`.
  - `test_failed_attack_is_never_called_a_disagreement`: the template contains no `Strongest disagreement` text; the rendered HTML for a sample where every attack failed contains `attack failed`.
  - `test_inferred_weights_are_labelled`.
  - Keep the template-token, no-external-URLs, browser-opening and CLI-usage tests from the copy.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement** the render changes and rewrite the template's script section to the new shape. Keep the CSS and design tokens from the copy, and keep embedding with `embed_json`.
- [ ] **Step 4: Verify.** Run `python -m pytest -q`: expected all pass. Extract the template's script and run `node --check` on it: expected no output and exit 0.
- [ ] **Step 5: Commit.** `git commit -am "critically-assess-adversarial: hearing report leads with verdict, plan and crux"`

### Task 8: Tamper suite

**Files:**
- Create: `tests/test_tamper.py`

**Interfaces:**
- Consumes: `sample_run.write_run`, `write_open_run`, `validate.validate_run`, `seal_thesis`, and `assemble.assemble`.

- [ ] **Step 1: Write the tests.** Each case from spec §11 is one test asserting a non-empty error list containing the named phrase:
  - thesis edited after its seal (`differs`);
  - attack before the thesis seal (`before`);
  - rebuttal before an attack (`before`);
  - deciding objection classed `priced_in` (`cannot decide`);
  - `overturned` with an unchanged verdict (`overturned`);
  - `survived` despite a conceded flip objection (`survived`);
  - supervisor-written thesis (`supervisor`);
  - missing `lean_answer` (`lean`);
  - valid attack dropped (`dropped`);
  - brief re-weighted after the seal (`brief.json differs`);
  - an attack reply from a role missing from the roster (`not in roster.json`).
- [ ] **Step 2: Run them.** `python -m pytest -q tests/test_tamper.py`. Expected: PASS. Every case is already enforced by Task 5. Any failure here is a Task 5 bug: fix it in `validate.py` and note the fix in the commit message.
- [ ] **Step 3: Commit.** `git add critically-assess-adversarial/tests/test_tamper.py && git commit -m "critically-assess-adversarial: tamper suite"`

### Task 9: SKILL.md and the contracts reference

**Files:**
- Rewrite: `SKILL.md`
- Rewrite: `reference/contracts.md`
- Modify: `tests/test_skill_md.py`

**Interfaces:**
- Consumes: the CLI commands from Task 5, `assemble.py` and `render.py` usage, the role ids and waves from Task 3, and the shapes from Tasks 2 and 6.

- [ ] **Step 1: Write the failing tests** in `test_skill_md.py`:
  - `test_description_says_when_to_use_this_over_critically_assess`: the description contains `critically-assess` and the word `challenge`.
  - `test_workflow_names_every_step`: the body contains `--seal-brief`, `--seal-thesis`, `rebuttal`, `SendMessage`, `user_lean.txt` and `never write the thesis`.
  - Keep `test_body_under_500_lines` and `test_every_referenced_file_exists`.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Write `SKILL.md`** following spec §5 step by step. Keep critically-assess's "When not to use", the subagent-tool check, the run-folder creation command, "Write for the reader" and the coherence pass.
  - The description states: use it to challenge a first answer on a decision with real stakes, where being wrong is costly; use critically-assess for a balanced pros-and-cons assessment.
  - Infrastructure failures are not attempts (§8).
  - The rebuttal continues the thesis agent with SendMessage, or falls back to a fresh agent and records `rebuttal_mode` (§12.1).

  Write `reference/contracts.md` from spec §6 and §7.
- [ ] **Step 4: Run the tests.** Run `python -m pytest -q`: expected all pass. Then run `git diff --quiet HEAD -- critically-assess`: expected exit 0.
- [ ] **Step 5: Commit.** `git commit -am "critically-assess-adversarial: SKILL.md and contracts for the hearing workflow"`

### Task 10: Evaluation harness

**Files:**
- Create: `eval/README.md`, `eval/cases/.gitkeep`, `eval/key/.gitkeep`, `eval/score.py`
- Create: `tests/test_eval_score.py`

**Interfaces:**
- Case file `eval/cases/<id>.json`: `{"id", "kind": "trap" | "control", "trap_type": "frame" | "base_rate" | "hidden_fact" | "values" | null, "prompt", "research": "none"}`.
- Key file `eval/key/<id>.json`: `{"id", "correct_decision", "accept": [decisions also counted correct], "crux": "the planted fact or missing option"}`.
- Run record `eval/runs/<condition>/<case-id>-<rep>.json`: `{"case", "condition": "plain" | "self-critique" | "hearing", "decision", "crux": str | null, "thesis_decision": str | null}`. For `plain` and `self-critique` the decision is extracted by hand, or by a blind judge, from the answer text.
- Produces:
  - `load(cases_dir, key_dir, runs_dir) -> tuple[dict, dict, list[dict]]`
  - `score(cases, keys, runs) -> dict`, with keys:
    - `catch` (`{condition: [hits, n]}` over traps);
    - `cave` (`{"hearing": [caves, n]}` over controls, where a cave means the thesis decision was correct and the final decision is not);
    - `crux_pairs` (a list of `{case, condition, key_crux, run_crux}` for human confirmation);
    - `pass_bar` (`{"catch_margin_ok": bool, "cave_ok": bool}`).
  - CLI `python eval/score.py` prints the three rates and the pass-bar result.

- [ ] **Step 1: Write the failing tests** with fixture cases written to `tmp_path`:
  - `test_catch_counts_traps_only`
  - `test_cave_needs_a_correct_thesis_and_a_wrong_final`
  - `test_accept_list_counts_as_correct`
  - `test_pass_bar`: hearing 10 of 16 against self-critique 6 of 16 gives a catch margin ≥ 4, so ok. 2 caves out of 8 is not ok.
  - `test_crux_pairs_list_every_hearing_trap_run`
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement `eval/score.py`.** Pass bar per §10: hearing catches minus self-critique catches ≥ 4, and hearing catches > plain catches; hearing caves ≤ 1. Write `eval/README.md` as the runbook from §10 and §12.4:
  - a separate agent drafts the 12 cases and their keys, and the user approves each key;
  - qualifying runs: 3 plain answers per case, keeping traps that fail at least 2 of 3 and controls that pass 3 of 3;
  - the pilot of 3 traps and 1 control comes first;
  - the main runs: 2 repeats per condition, with launches spaced under the 20-subagent cap;
  - the supervisor and judges never read `eval/key/`;
  - the trigger-overlap check from §11: give 20 prompts to an agent along with both skill descriptions and record which skill it picks for each.
- [ ] **Step 4: Run them.** Run `python -m pytest -q`: expected all pass. Run `git diff --quiet HEAD -- critically-assess`: expected exit 0.
- [ ] **Step 5: Commit.** `git add -A critically-assess-adversarial/eval critically-assess-adversarial/tests/test_eval_score.py && git commit -m "critically-assess-adversarial: evaluation scoring and runbook"`

---

**Not in this plan (by design):**
- Drafting the 12 evaluation cases.
- Running the pilot and the full evaluation.

These follow the runbook from Task 10 once the code is in, because they need the user's approval of the answer keys (§12.4).
