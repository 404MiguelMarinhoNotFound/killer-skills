# Reference notes

Distilled from the files in `.refs/` (see `.refs/SOURCES.md`). Everything here is paraphrased. Nothing from `.refs/` ships.

## Patterns we adopt
| Pattern | Source | Lands in |
|---|---|---|
| Roles are thinking styles picked to pull against each other, not job titles | llm-council-remy.md | roles/*.md `tension_with` |
| Look for workspace context (CLAUDE.md, files the user pointed at) before framing the question | llm-council-remy.md | SKILL.md step 2 |
| Subagents receive only the question and the context they need, never the conversation (anti-anchoring) | council-ecc.md | SKILL.md step 6 |
| Supervisor records its own position, top reasons and main risk before reading the council | council-ecc.md | SKILL.md step 4, precommit.json |
| Synthesis guardrails: justify every dismissal, surface the strongest dissent, admit when a voice changed the outcome, treat two voices against your position as a real signal | council-ecc.md | SKILL.md step 8 |
| One shared brief with the exact question, background, constraints and expected report format | council-warp.md (brief before launching) | brief.json |
| Structured member reports with evidence, recommendation, confidence and unknowns | council-warp.md | roles/_contract.md |
| Compare reports by evidence quality, not by vote count | council-warp.md | SKILL.md step 8 |
| Chase missing evidence with a focused follow-up rather than accepting a weak report | council-warp.md | SKILL.md step 7 (we relaunch the role once with the errors) |
| Explicitly ask what every voice missed | llm-council-remy.md | result.blind_spots |
| The synthesizer may side with a lone dissenter when its reasoning is strongest | llm-council-remy.md | SKILL.md step 8 |
| Parallel first opinions, shown side by side before the final answer | karpathy-readme.md, karpathy-council.py | Council section of report.html |
| Description carries triggers and when-not-to-use | anthropic-skill-creator.md | SKILL.md frontmatter |
| Keep SKILL.md lean, push detail into files loaded on demand | anthropic-skill-creator.md | reference/contracts.md |

## Rejected for v1
- Anonymized peer-review round (Karpathy, Remy): doubles subagent cost; the supervisor's blind-spot pass keeps its main value.
- Separate chairman subagent (Remy, Karpathy): the supervisor already holds the research and the pre-commitment.
- Approval gate before launch (Warp): the brief is shown in the report instead.
- Cross-vendor model roster (Warp, Karpathy): v1 mixes Opus and Sonnet only.
- Remy's output instructions: step 5 forbids an HTML report while the closing notes ask for a clean HTML one. We pick one answer (always an HTML report plus a short chat summary) and state it once.

## Role lineage
| Our role | Drawn from |
|---|---|
| contrarian | Remy Contrarian + ECC Critic |
| first-principles | Remy First Principles Thinker + ECC Skeptic |
| executor | Remy Executor + ECC Pragmatist |
| expansionist | Remy Expansionist |
| outsider | Remy Outsider |
| analyst | Ours: the neutral ledger none of the sources has |
