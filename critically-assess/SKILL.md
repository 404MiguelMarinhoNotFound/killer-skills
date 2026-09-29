---
name: critically-assess
description: Critically assess a single idea (against the status quo) or compare several options, using a council of 3-5 role-based subagents plus a neutral analyst subagent. Produces weighted criterion scores, a merged pros and cons ledger, the strongest dissent, blind spots and a verdict, rendered as a minimal HTML report. Use when the user says "critically assess", "assess this idea", "pressure-test this", "compare these options", "pros and cons of", or brings a real decision with stakes and tradeoffs. Also use it whenever the user asks you to compare or choose between named alternatives (frameworks, databases, vendors, tools, strategies) for a stated purpose, such as "compare X, Y and Z for our API" or "which of these should we pick", even if they never say "assess". Do not use for factual questions, creation tasks or trivial choices.
---

# Critically Assess

You are the supervisor. You research, write one neutral brief, commit to your own view, run a council of independent subagents, then write a verdict judged on evidence rather than on how many voices agree. Every run leaves a folder of JSON files and one HTML report.

`<SKILL_DIR>` below means the base directory Claude Code reports when this skill loads.

## When not to use
- The question has one right answer (a fact, a lookup): answer directly.
- The user wants something made (write, build, draft): do the task.
- The choice is trivial or instantly reversible: give a one-line opinion.

## Workflow

### 1. Detect the mode
- One idea, plan or proposal: mode `single`. Option A is the idea, option B is "Status quo".
- Two or more alternatives: mode `multi`. Label them A, B, C in the order the user gave them.
- If there is nothing concrete to assess, ask one clarifying question. Otherwise do not ask anything: there is no approval step, and the brief is shown in the report instead.

### 2. Research it yourself
Collect only what can change the assessment:
- Files or links the user attached or mentioned.
- For codebase questions, send broad scans to the built-in `Explore` subagent, then read the key files it points to yourself.
- For facts about the outside world (prices, limits, benchmarks, current state), use WebSearch and WebFetch.
Record the source of every fact you plan to rely on. Stop once the options, constraints and stakes are clear.

### 3. Write the brief
Create the run directory with one Bash command, using the real clock rather than a made-up time: `D=".critically-assess/runs/$(date +%Y%m%d-%H%M%S)-<slug>"; mkdir -p "$D/reports" && realpath "$D"`. Copy the printed absolute path exactly and use it as `<run_dir>` for every later write and command; never retype it from memory. Read `<SKILL_DIR>/reference/contracts.md` and write `brief.json`. Derive 3 to 6 criteria from what the user is trying to achieve and what is at stake, weight them, and justify each weight in one line. Keep the brief neutral.

### 4. Commit to your own view
Before launching anyone, write `precommit.json` with your position, your three strongest reasons and your main risk. No subagent ever sees it. It exists so your synthesis cannot quietly mirror the council.

### 5. Pick the roster
Run `python "<SKILL_DIR>/scripts/role_library.py"` to list the library. Pick 3 to 5 council roles that fit this topic, plus `analyst`, who is always included. Favour roles that pull against each other (`tension_with`). For each pick, note one line on why it is on this council and which model it runs on: the role's `model` unless you have a reason to override.

### 6. Launch the council in parallel
Send one message containing one subagent call per roster role (the `Agent` tool; older Claude Code versions call it `Task`), with `subagent_type: general-purpose` and the roster's `model`. Each prompt contains, in this order:
1. The role file's body: `<SKILL_DIR>/roles/<id>.md` without its frontmatter.
2. For council roles only: the contents of `<SKILL_DIR>/roles/_contract.md`. The analyst's contract is already in its role file.
3. `BRIEF:` followed by the full `brief.json`.
4. This instruction, with the role's id filled in: "Your role id is `<id>`; put exactly that in the `role` field. Work only from the brief. Do not browse, read files or edit anything. Reply with the JSON object only."

Never include the conversation, your research notes or `precommit.json`. If the tool rejects the `model` parameter, relaunch without it and record the model as `inherited`.

### 7. Save and validate
Save each reply verbatim to `reports/<role-id>.raw.txt`, then run:

    python "<SKILL_DIR>/scripts/validate.py" <run_dir>

It converts every raw reply to `reports/<role-id>.json` and checks it. For any role with errors, relaunch that single role once, with the error lines appended to its prompt. If it fails a second time, drop the role and add it to `unknowns`.

### 8. Synthesize
Read every report, then write `result.json` as described in `reference/contracts.md`:
- Weigh evidence quality, not the number of voices that agree.
- Never dismiss a council view without saying why.
- If two or more roles argued against your pre-commitment, treat that as a real signal and answer it directly. If a role changed your mind, say so in `drift`.
- Always record the strongest dissent, including one you reject. You may side with a lone dissenter when its reasoning is strongest.
- `blind_spots` must name at least one thing no voice raised. Look for it on purpose: second-order effects, the cost of reversing, who else is affected, what happens if the central assumption is wrong.
- Give a real verdict. The only form of "it depends" is `conditional-go` with explicit conditions.
- Give one first step, not a list.

Run `validate.py` again and fix `result.json` until it prints OK.

### 9. Render and answer
Run `python "<SKILL_DIR>/scripts/render.py" <run_dir>`. It writes `report.html` and prints a short summary. Reply in chat with that summary and the report path. Do not paste the full report into chat.

## Anti-patterns
- Letting a subagent see another subagent's output, the conversation or your pre-commitment.
- Launching subagents one after another instead of in one parallel message.
- Treating the analyst's scores as the verdict. They are an input; the verdict is yours.
- Smoothing over disagreement to make the verdict look clean.
- Pros and cons that would apply to any option.
