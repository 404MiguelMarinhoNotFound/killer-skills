---
name: critically-assess
description: Critically assess a single idea (against the status quo) or compare several options, using a council of 3-5 role-based subagents plus a neutral analyst subagent. Produces weighted criterion scores, a merged pros and cons ledger, the strongest dissent, blind spots and a verdict, rendered as a minimal HTML report. Use when the user says "critically assess", "assess this idea", "pressure-test this", "compare these options", "pros and cons of", or brings a real decision with stakes and tradeoffs. Also use it whenever the user asks you to compare or choose between named alternatives (frameworks, databases, vendors, tools, strategies) for a stated purpose, such as "compare X, Y and Z for our API" or "which of these should we pick", even if they never say "assess". Do not use for factual questions, creation tasks or trivial choices.
---

# Critically Assess

You are the supervisor. You research, write one neutral brief, commit to your own view, run a council of independent subagents, then write a verdict judged on evidence rather than on how many voices agree. Every run leaves a folder of JSON files and one HTML report.

`<SKILL_DIR>` below means the base directory Claude Code reports when this skill loads. `<working_dir>` means the absolute path of the current working directory. The scripts need Python 3.10+ and nothing else; if `python` is not found, use `python3`.

## When not to use
- The question has one right answer (a fact, a lookup): answer directly.
- The user wants something made (write, build, draft): do the task.
- The choice is trivial or instantly reversible: give a one-line opinion.

Once this skill is running, finish the whole workflow below. If partway through you think a full council is not worth it, say so and ask the user; never quietly swap in your own quick answer.

## Workflow

### 1. Detect the mode
- One idea, plan or proposal: mode `single`. Option A is the idea, option B is "Status quo".
- Two or more alternatives: mode `multi`. Label them A, B, C in the order the user gave them.
- If there is nothing concrete to assess, ask one clarifying question. Apart from that and the research question in step 2, do not ask anything: there is no approval step, and the brief is shown in the report instead.

### 2. Ask whether to research, then research
Research is optional and the user decides. If the user already said what research they want, use that and don't ask. Otherwise ask one question with the `AskUserQuestion` tool: "Do you want me to search online for relevant facts or similar approaches, gather knowledge from this repo to pass to the council, or both? Or are these options hypothetical, so I should work only from what you've told me?" Offer four choices: `Online`, `Repo`, `Both`, `Neither: hypothetical`. Put first, marked recommended, the choice that fits: `Both` when the options are real products or code in this repo, `Online` for real products outside it, `Repo` for internal code choices, `Neither` for personal or conceptual questions. If you cannot ask (for example in a non-interactive run), treat the answer as `Neither` and add "no research was done" to `unknowns`. The answer also sets what the council may look up in step 6, and it goes into the brief as `research`: `online`, `repo`, `both` or `none`.

Then gather the shared facts every voice should start from, within what the user chose, and only what can change the assessment. Each council voice can look up more for its own lens later, so you do not need to cover everything:
- `Repo`: files the user attached or mentioned, and the files that bear on the options. Send broad scans to the built-in `Explore` subagent, then read the key files it points to yourself.
- `Online`: current facts that decide the case (prices, limits, maintenance status, known failure stories, how others solved the same problem), using WebSearch and WebFetch. For technical options, prefer each technology's official documentation for the version in play; open its GitHub repository only when the docs can't answer, such as for open issues, real behaviour in source, or maintenance activity.
- `Neither`: use only the user's message and files they attached.

Record the source of every fact you rely on. A fact you did not check gets the source `general knowledge (unverified)`, never a document name you did not open. Stop once the options, constraints and stakes are clear.

### 3. Write the brief
Create the run directory with one Bash command, using the real clock rather than a made-up time: `D=".critically-assess/runs/$(date +%Y%m%d-%H%M%S)-<slug>"; mkdir -p "$D/reports" && realpath "$D"`, where `<slug>` is 2-5 lowercase words joined by hyphens (letters, digits and hyphens only). If that command is blocked, run `date +%Y%m%d-%H%M%S` on its own and build the folder name from its output; never invent the timestamp. Copy the printed absolute path exactly and use it as `<run_dir>` for every later write and command; never retype it from memory. Read `<SKILL_DIR>/reference/contracts.md` and write `brief.json`. Derive 3 to 6 criteria from what the user is trying to achieve and what is at stake, weight them, and justify each weight in one line. Keep the brief neutral. The report shows the brief to the reader, so write it the way "Write for the reader" in step 8 describes, not as notes.

### 4. Commit to your own view
Before launching anyone, write your position, your three strongest reasons and your main risk to a sealed file outside the working directory, so a council voice that reads the repository cannot find it: `${TMPDIR:-/tmp}/critically-assess-sealed/<run-id>.json`, where `<run-id>` is the run folder's name. Print its absolute path and reuse it exactly. No subagent ever sees it. It exists so your synthesis cannot quietly mirror the council. The report later shows this view next to where you ended up, so write it in full sentences a reader can follow.

### 5. Pick the roster
Run `python "<SKILL_DIR>/scripts/role_library.py"` to list the library. Pick 3 to 5 council roles that fit this topic, plus `analyst`, who is always included. Favour roles that pull against each other (`tension_with`). For each pick, note one line on why it is on this council and which model it runs on: the role's `model` unless you have a reason to override.

### 6. Launch the council in parallel
Send one message containing one subagent call per roster role (the `Agent` tool; older Claude Code versions call it `Task`), with `subagent_type: general-purpose` and the roster's `model`. Keep each prompt short, so all calls go out at once; every voice reads its own instructions and the brief from disk. Each prompt contains, in this order, with the placeholders filled in:
1. "You are <name> (role id `<id>`), one voice on an independent decision council. Every voice gets the same brief and a different job, and the supervisor weighs the replies by the quality of their evidence, not by how many agree. You will never see the other replies, so do your own job fully and leave the other jobs to the voices that own them."
2. For a council role: "Read these three files in full before anything else, ignoring the frontmatter at the top of the first: `<SKILL_DIR>/roles/<id>.md` (your role), `<SKILL_DIR>/roles/_contract.md` (your output contract) and `<run_dir>/brief.json` (the brief)." For the analyst, the same with only the role file and the brief, because its contract is inside its role file.
3. The access line that matches `brief.research`, for council roles:
   - `both`: "You may search the web and read files in the repository at `<working_dir>` if your lens needs a fact the brief does not settle. You do not have to."
   - `online`: "You may search the web if your lens needs a fact the brief does not settle. You do not have to. Do not read other files."
   - `repo`: "You may read files in the repository at `<working_dir>` if your lens needs a fact the brief does not settle. You do not have to. Do not search the web."
   - `none`, and always for the analyst: "Work from the brief alone: do not search the web or read other files."
4. "Put exactly `<id>` in the `role` field. Never read `.critically-assess/` apart from your brief, and never edit, write or run anything. Where you are missing something you need, say so and name the assumption you made. End your reply with the JSON object; nothing after it is read. Before you answer, think the problem through from your role's angle. Then reread each item you wrote as a reader who sees only that item, and unpack any that would not make sense alone."

Never include the conversation, your research notes or the sealed pre-commitment. If the tool rejects the `model` parameter, relaunch without it and record the model as `inherited`.

### 7. Save and validate
Save each reply verbatim to `reports/<role-id>.raw.txt`, then run:

    python "<SKILL_DIR>/scripts/validate.py" <run_dir>

It converts every raw reply to `reports/<role-id>.json` and checks it; every error line starts with the role it belongs to. For any role with errors, relaunch that single role once, with its error lines appended to the original prompt under `YOUR PREVIOUS REPLY WAS REJECTED:`, and overwrite its `.raw.txt` with the new reply.
- A council role that fails twice is dropped: move its `.raw.txt` (and `.json`, if any) into `reports/dropped/`, leave it out of the roster, and add "<role> gave no usable report" to `unknowns`. Validation ignores `reports/dropped/`. If dropping would leave fewer than 3 council roles, launch a replacement role from the library instead.
- The analyst cannot be dropped, because the scores come from it. If it fails twice, write its report yourself in the analyst format, start every `rationale` and `evidence` with `Supervisor:`, save it as `reports/analyst.raw.txt`, set the analyst's roster model to `supervisor`, and add "analyst scores written by the supervisor" to `unknowns`.

Re-run `validate.py` until it prints OK before moving on. Then move the sealed pre-commitment into `<run_dir>/precommit.json`; the council is finished, so it no longer needs hiding.

### 8. Synthesize
Read every report, then write `result.json` as described in `reference/contracts.md`:
- Weigh evidence quality, not the number of voices that agree. Each council position is the verdict of one lens, so a split council is expected; agreement across lenses that were built to disagree is the stronger signal.
- Never dismiss a council view without saying why.
- Rank evidence by its tag: `Source:` and `Brief:` facts first, then `Mechanism:` reasoning, then `Knowledge:` recall. Every voice shares the same training, so a `Knowledge:` claim raised by several voices counts once. When the verdict would rest on a `Knowledge:` claim, check it yourself if the research setting allows it; otherwise add it to `unknowns`. When two `Source:` items disagree, say which you trust and why.
- If two or more roles argued against your pre-commitment, treat that as a real signal and answer it directly. If a role changed your mind, say so in `drift`.
- Give every ledger item a `point` as well as its `claim`. The report lists the points under each option's name, one line each, so a reader can scan them; the full claim opens when they click. The point says what the item is, not why: "Adds a Redis server the team has never run." The claim then explains it.
- Always record the strongest dissent, including one you reject. You may side with a lone dissenter when its reasoning is strongest.
- `blind_spots` must name at least one thing no voice raised. Look for it on purpose: second-order effects, the cost of reversing, who else is affected, what happens if the central assumption is wrong.
- Give a real verdict. The only form of "it depends" is `conditional-go` with explicit conditions.
- Give one first step, not a list.

#### Write for the reader
Everything in `result.json` ends up in the report, and the reader never saw the brief, the council's replies or your notes. Rewrite what you take from the reports instead of pasting it.
- Call each option by its name. The letters A, B, C are ids for the files only.
- Leave out this skill's own vocabulary: brief, pre-commitment, council voice, lens, roster, step numbers, file names. Say what you mean ("before hearing the council, I leaned towards...").
- Explain, don't compress. There is no word limit: length follows the idea. A simple point gets a short sentence, and that sentence must still be complete and clear. A big idea gets as many words and sentences as it takes to explain.
- Unpack each concept instead of naming it. A reader follows a claim when they can see three things: what the thing is, what happens and through which chain of events, and why that matters for this user. A string of nouns ("migration risk", "ops burden", "lock-in") only names a concept; write out what it means here.
- Make every item stand alone. The report shows each claim, score reason, blind spot and unknown on its own, so the reader cannot see the sentence before it. Only a ledger `point` may leave out the option's name, because the report lists it under that name. Name the subject every time, never open with "It", "This", "That" or "They", and never point to "above" or "the same".
- Write sentences, not notes: no arrows, slashes, dropped verbs or chains of clauses joined by semicolons. Where ideas connect, say how ("because", "so", "which means").
- Put the point first, then the reason. Use the active voice and everyday words.
- Spell out an acronym the first time, as in "point-in-time recovery (PITR)", unless the user used it.
- Give numbers with their unit and what they mean: "about 3 weeks of work for the 3-person team".

Two rewrites showing the pattern (the topic is only an illustration):
- Before: "None: I precommitted to B on cost and hiring lead time; the council agreed." After: "No change. Before hearing the council, I leaned towards hiring a contractor, and every role agreed."
- Before: "Adds a broker (RabbitMQ -> Erlang runtime, clustering, TLS certs) to a stack promising 'one database and nothing else'; not in staging; an outage stops checkout at step 3." After: "Adding RabbitMQ means running a second system next to the database. If it goes down, customers cannot check out."
- Before: "Lower ops burden vs. the incumbent; migration risk real." After: "With the managed service, nobody on the team has to patch or restart servers any more. The cost is the move itself: two years of order data have to be copied over without taking the shop offline."

#### Coherence pass
Before validating, read `result.json` once more as a newcomer who knows only the user's question. Take each reader-facing string on its own: the verdict, conditions, first step, drift, dissent, every ledger claim, every score reason, every blind spot and unknown. For each, ask: could this reader say back, in their own words, what it claims and why it matters? If not, the fix is almost never to cut or split. Find the concept the sentence leans on, and explain it: name the thing, say what happens, say why it matters here. Check the whole report reads as one story too: the verdict, the pros and cons and the dissent should use the same names for the same things.

Then run `validate.py` again and fix `result.json` until it prints OK. It checks structure only (fields, ids, the score grid), never the writing: how clearly the report reads is down to the coherence pass.

### 9. Render and answer
Run `python "<SKILL_DIR>/scripts/render.py" <run_dir>`. It writes `report.html`, prints a short summary, and opens the report in the user's default browser when the machine has one (add `--no-open` if the user asked not to). Reply in chat with that summary, written the same plain way. If it printed "Opened in your default browser", say so; otherwise give the `file://` link it printed so the user can open it. Do not paste the full report into chat.

## Anti-patterns
- Letting a subagent see another subagent's output, the conversation or your pre-commitment, including by leaving the pre-commitment inside the working directory while the council runs.
- Launching subagents one after another instead of in one parallel message.
- Treating the analyst's scores as the verdict. They are an input; the verdict is yours.
- Smoothing over disagreement to make the verdict look clean.
- Pros and cons that would apply to any option.
