# Writing subagent role prompts

Consolidated on 2026-09-29 from AI-engineering sources (listed at the end). Everything is paraphrased. Each rule notes where it came from and how it applies to the `roles/*.md` files in this skill.

## 1. The prompt is the subagent's whole world
A subagent starts with an empty context. It never sees the conversation, earlier files or the supervisor's reasoning. Anything it needs must be in the role file, the contract or the brief. "As discussed" means nothing to it. [CC-docs, MA]
- **Here:** the brief must carry every fact a role relies on, and a role must never refer to anything outside its own prompt.

## 2. Every delegation states four things
These are the objective, the output format, which tools and sources to use, and the boundaries of the task, including what belongs to another agent. Without explicit boundaries, parallel agents duplicate each other and leave gaps. [MA]
- **Here:** each role says what it owns and names what it leaves to other roles ("the Contrarian owns downside"). The fixed tool rule is to work only from the brief.

## 3. Write at the right altitude
Avoid two extremes: brittle if-then scripts on one side, and vague encouragement that assumes shared context on the other. Aim for the smallest set of high-signal instructions that fully defines the behaviour, framed as heuristics the model can apply to cases you did not foresee. Minimal does not have to mean short. [CE]
- **Here:** a role is a lens plus a few sharp duties, not a checklist of every situation.

## 4. Explain why
Instructions that come with their reason generalise better than bare commands. The model can then apply the intent to cases the rule did not name. [BP]
- **Here:** give a one-clause reason where a duty is not self-evident, for example "the favourite is where a missed flaw costs the most".

## 5. Say what to do, not only what to avoid
Positive instructions steer better than prohibitions, and positive examples of the wanted style beat lists of don'ts. Keep a short "must not" list for the real failure modes that were observed. [BP, OPUS5]
- **Here:** "You must" carries the behaviour. "You must not" stays short and targets observed failures such as generic points and invented facts.

## 6. A role line helps; make it a task lens, not a persona
Even one sentence of role focuses behaviour and tone. The role should describe how to think about the task. Demographic or character-style personas can hurt accuracy: one study measured up to about 26% degradation from task-irrelevant persona cues. [ROLE, PERSONA]
- **Here:** roles are thinking styles tied to the decision ("find the flaw that sinks it"), never characters with backstories.

## 7. Use calm, direct language
Recent Claude models follow the system prompt closely. Shouting ("CRITICAL", "you MUST", all caps) now causes over-application rather than compliance. OpenAI's guide likewise says caps and incentives are unnecessary. [BP, GPT41]
- **Here:** use plain imperatives. The section headings "You must" and "You must not" are structural labels required by the linter, not emphasis.

## 8. Models follow instructions literally
Current models do what the prompt says, not what it implies. A rule that is only hinted at will not be applied. [GPT41, BP]
- **Here:** state every expectation outright. For example, write "exactly one per_option entry per option, the status quo included" rather than expecting the model to infer coverage.

## 9. Structure and ordering
- Separate kinds of content with Markdown headers or XML tags: role, instructions, output format, examples, input data. [CE, BP, GPT41]
- A good default order is role and objective, then instructions, output format, examples, and finally the input. [GPT41]
- Place long input data (our brief) where it is clearly delimited. Close with the one instruction that matters most, because the final instructions carry the most weight. [BP, GPT41]
- When two instructions conflict, the later one tends to win. Read the assembled prompt end to end and remove contradictions. [GPT41]
- **Here:** the assembled prompt is opening line, then lens and duties, then contract, then `BRIEF:`, then the closing instruction. The role file and the contract must not contradict each other.

## 10. Examples are powerful, and they get copied
A few diverse, canonical examples steer format and tone more reliably than prose. Put them in clearly marked blocks. Any behaviour an example shows should also be stated as a rule. Models copy example wording, so vary examples or keep them schematic. [BP, CE, GPT41]
- **Here:** the contract shows the JSON shape with placeholders. Do not add a filled-in example about a real topic, because the council would anchor on it.

## 11. JSON answers to reasoning tasks
When a model must reason and answer in JSON, it may skip the reasoning or write a draft before the final JSON. [SONNET55]
- A closing line such as "think the problem through before you answer" raises accuracy.
- Keep the reasoning and the answer in separate places, so a draft can never be mistaken for the answer.
- **Here:** the closing instruction asks the role to think first in its conversation, then write only the final JSON object to its own reply file. `scripts/validate.py` reads that file as strict JSON, so a draft, a code fence or a note around the object is an error rather than something to guess around.

## 12. Don't add work the model already does
Opus-class models check their own work. Extra "double-check your answer" or verification steps add cost without adding quality. Instructions that limit output ("only report high-severity issues") are followed literally and lose findings. It is better to ask for everything and filter later. [OPUS5]
- **Here:** no "verify your answer" lines. Ask roles for their full view within the word budget, and leave filtering to the supervisor.

## 13. Keep role diversity from collapsing
Role-played agents drift toward early consensus and moderate positions even when given different personas. Diverse roles pay off only if each is pushed to hold its angle. [PERSONA, CHATEVAL]
- **Here:** each role takes its lens all the way and names the fact that would flip its position. The Analyst supplies the balance, so no other role has to.

## 14. Return a distilled result
A subagent may do a lot of work, but it should hand back a compact, structured summary. That keeps the supervisor's context clean and makes outputs comparable. [CE, CC-docs]
- **Here:** return one JSON object with fixed fields. Distilled means no padding or repetition, not compressed wording: the council text is shown to the user as written, so each item gets the words it needs to be clear on its own. An earlier 300-word budget pushed voices into note-style shorthand and was removed.

## 15. Evaluate early on real cases
Start with a small set of realistic cases, judge outputs against a rubric (an LLM judge plus a human look), and treat prompt wording as the main lever. Small phrasing changes move behaviour a lot. [MA]
- **Here:** the three smoke cases in Task 7 are the evaluation set. Re-run them after every prompt change.

## Sources
- [MA] Anthropic Engineering, *How we built our multi-agent research system*: https://www.anthropic.com/engineering/multi-agent-research-system
- [CE] Anthropic Engineering, *Effective context engineering for AI agents*: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- [BP] Claude Docs, *Prompting best practices*: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- [SONNET55] Claude Docs, *Prompting Claude Sonnet 5.5*: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5
- [OPUS5] Claude Docs, *Prompting Claude Opus 5*: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5
- [ROLE] Claude Docs, *Giving Claude a role with a system prompt*: https://docs.anthropic.com/en/docs/give-claude-a-role
- [CC-docs] Claude Code Docs, *Create custom subagents*: https://code.claude.com/docs/en/sub-agents
- [GPT41] OpenAI Cookbook, *GPT-4.1 Prompting Guide*: https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide
- [PERSONA] *From Biased Chatbots to Biased Agents: Examining Role Assignment Effects on LLM Agent Robustness* (arXiv 2602.12285): https://arxiv.org/html/2602.12285
- [CHATEVAL] Chan et al., *ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate* (ICLR 2024): https://proceedings.iclr.cc/paper_files/paper/2024/file/25cc3adf8c85f7c70989cb8a97a691a7-Paper-Conference.pdf
