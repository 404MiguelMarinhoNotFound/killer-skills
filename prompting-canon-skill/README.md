# The Prompting Canon

A comprehensive Agent Skill for applying **current** prompt-engineering best practices from Anthropic (Claude), OpenAI (GPT-5 family), and Google (Gemini 3), plus durable patterns from PromptingGuide.ai.

> **v2.0 (June 2026):** Updated for the current model generation. Adds Google Gemini, reframes reasoning as a *parameter* (effort / thinking_level / verbosity) rather than a prompt, marks assistant prefill as legacy (rejected on Claude 4.6+), corrects the temperature guidance, fixes long-context ordering (data top / query end), and adds a deep agentic & context-engineering section plus a vendor-generic prompt-optimization workflow.

---

## What This Skill Does

This skill teaches AI coding assistants (Cursor, Claude, GitHub Copilot) how to craft high-quality prompts for LLMs. It provides:

- ✅ **Complete prompting methodology** from industry leaders
- ✅ **12 ready-to-use templates** for common scenarios
- ✅ **Before/after examples** showing real improvements
- ✅ **Automated validation** to check prompt quality
- ✅ **Quick reference** for rapid application
- ✅ **Decision frameworks** for choosing techniques

---

## Installation

### For Cursor

```bash
# Copy to project skills directory (recommended)
cp -r prompting-canon-skill /path/to/your/project/.cursor/skills/

# OR copy to global skills directory
cp -r prompting-canon-skill ~/.cursor/skills/
```

Enable Nightly release in Cursor:
1. Settings > Beta
2. Update channel → Nightly
3. Restart Cursor

### For Claude.ai

```bash
# Create zip file
cd prompting-canon-skill
zip -r ../prompting-canon-skill.zip .
```

Then:
1. Go to Claude.ai → Settings → Features
2. Upload `prompting-canon-skill.zip`
3. Enable in conversations

### For GitHub Copilot (VS Code)

```bash
# Copy to project
cp -r prompting-canon-skill /path/to/project/.github/skills/

# OR copy to personal
cp -r prompting-canon-skill ~/.copilot/skills/
```

Reload VS Code.

---

## How It Works

### Automatic Activation

The skill activates when you work on prompts or mention:
- "prompt engineering", "improve this prompt", "optimize this prompt"
- "LLM", "GPT", "GPT-5", "Claude", "Gemini"
- "reasoning effort", "thinking level", "verbosity", "extended/adaptive thinking"
- "few-shot", "RAG", "structured outputs", "function calling"
- "agentic", "tool use", "subagents", "context engineering"
- "prompt quality", "hallucinations"

### Usage Examples

**Example 1: Get a template**
```
You: "Give me a prompt template for document Q&A"
AI: [Loads prompting-canon skill]
    [Provides RAG template from templates/prompt-templates.md]
```

**Example 2: Improve a prompt**
```
You: "Improve this prompt: 'Explain machine learning'"
AI: [Loads prompting-canon skill]
    [Applies doctrine principles]
    [Returns structured, improved version]
```

**Example 3: Debug issues**
```
You: "My agent keeps hallucinating facts"
AI: [Loads prompting-canon skill]
    [Suggests RAG + quote-then-analyze pattern]
    [Shows implementation example]
```

---

## Skill Contents

```
prompting-canon-skill/
├── SKILL.md                           # Lean entry point (routes to references)
│   ├── Core principles (outcome-first, control-surface-first)
│   ├── The Control Surface (effort / thinking / verbosity)
│   ├── Key techniques (current status; CoT demoted, prefill legacy)
│   ├── Agentic & context engineering + optimization workflow
│   └── Corrected temperature guidance, anti-patterns, picker
│
├── templates/
│   └── prompt-templates.md            # 15 ready-to-use templates
│       ├── Classification, RAG, Reasoning, Code, Writing...
│       ├── Outcome-First (reasoning model)        [new]
│       ├── Long-Horizon Agentic Task              [new]
│       └── Prompt Optimization (advisory)         [new]
│
├── examples/
│   └── before-after-examples.md       # 12 improvement case studies
│       ├── Vague → Specific, Few-shot, Grounded...
│       ├── Over-Engineered → Outcome-First         [new, 2026]
│       └── Manual CoT → the Thinking Knob          [new, 2026]
│
├── references/
│   ├── prompting-canon.md             # Full canon (control surface, agentic deep-dive,
│   │                                    optimization workflow, dated model landscape)
│   └── quick-reference.md             # One-page cheat sheet
│
└── scripts/
    └── prompt-validator.py            # Quality validation tool
```

---

## Quick Start

### 1. Install the Skill
Follow installation instructions above.

### 2. Try It Out

Open Cursor and ask:
```
"Show me the prompt engineering quick reference"
```

The AI will load the skill and provide the cheat sheet.

### 3. Apply to Real Work

```
"Using the prompting doctrine, create a prompt for 
classifying customer support tickets by urgency"
```

The AI will:
1. Choose appropriate template
2. Apply best practices
3. Add examples and constraints
4. Return production-ready prompt

---

## Use Cases

### For Developers

**Use Case: Code Generation Prompts**
```
"Create a prompt that generates Python functions with 
tests and documentation"
```

→ AI provides structured prompt with:
- Language-specific constraints
- Output format (code + tests)
- Error handling requirements
- Style guide references

**Use Case: Code Review Prompts**
```
"Help me write a prompt for AI code review focusing on 
security and performance"
```

→ AI provides:
- Security checklist
- Performance criteria
- Structured output format
- Examples of good/bad code

### For Data Scientists

**Use Case: Data Analysis Prompts**
```
"I need a prompt that analyzes sales data and finds 
actionable insights"
```

→ AI provides:
- Analysis framework
- Key metrics to examine
- Structured output format
- Visualization recommendations

**Use Case: RAG Implementation**
```
"Build a prompt for Q&A over our documentation with 
citations"
```

→ AI provides:
- RAG pattern with context tags
- Citation requirements
- Hallucination prevention
- Answer format

### For Product Managers

**Use Case: User Research Analysis**
```
"Create a prompt that summarizes user feedback and 
extracts feature requests"
```

→ AI provides:
- Structured extraction prompt
- Classification categories
- Priority scoring
- Output format for roadmapping

### For Content Creators

**Use Case: Content Generation**
```
"I need a prompt for writing SEO-optimized blog posts 
about tech topics"
```

→ AI provides:
- Audience definition
- Tone guidelines
- SEO requirements
- Structure template

---

## Advanced Usage

### Validate Prompts

```bash
# Validate a prompt
python scripts/prompt-validator.py "Your prompt here"

# Validate from file
python scripts/prompt-validator.py --file my-prompt.txt

# Interactive mode
python scripts/prompt-validator.py --interactive
```

Output:
```
PROMPT QUALITY REPORT
Overall Score: 78/100 - GOOD ✅

⚠️  WARNINGS (2):
  [Clarity] Vague terms found: helpful, accurate
    → Fix: Replace with specific, measurable criteria
  
  [Format] No output format specified
    → Fix: Add 'Output Format:' section with example
```

### Chain with Other Skills

Combine with other skills for powerful workflows:

```
# Use with databricks-ai-agents skill
"Using prompting-canon, create an evaluation prompt 
for my Databricks agent"

# Use with code generation
"Apply prompting best practices to generate a prompt 
for React component creation"
```

---

## Learning Path

### Beginner (Week 1)
1. Read `references/quick-reference.md`
2. Try 3 templates from `templates/prompt-templates.md`
3. Review 5 before/after examples
4. Validate your prompts with the script

### Intermediate (Week 2-3)
1. Study specific techniques in `SKILL.md`
2. Apply to your actual use cases
3. Create custom templates
4. Build prompt evaluation datasets

### Advanced (Month 2+)
1. Read full `references/prompting-canon.md`
2. Implement prompt chaining workflows
3. Build domain-specific prompt libraries
4. Optimize for production (caching, costs)

---

## Best Practices

### DO
✅ Start with templates and customize
✅ Test prompts with 3+ examples before production
✅ Use the validator to catch issues early
✅ Keep a library of your best prompts
✅ Version control your prompts
✅ Measure improvements empirically

### DON'T
❌ Skip examples for complex tasks
❌ Use vague instructions ("be helpful")
❌ Deploy without testing edge cases
❌ Ignore the anti-patterns list
❌ Mix instructions and data without delimiters
❌ Forget to specify output format

---

## Troubleshooting

### Skill Not Loading

**Problem:** AI doesn't seem to use the skill

**Solutions:**
1. Verify skill directory location
2. Check SKILL.md has valid YAML frontmatter
3. Restart Cursor/VS Code
4. Use explicit trigger: "Using the prompting-canon skill..."

### Performance Issues

**Problem:** Skill makes responses slower

**Solutions:**
1. Skill loads on-demand, not always
2. Reference files loaded only when needed
3. For fast queries, use quick-reference directly
4. Templates are lightweight

### Validation Script Issues

**Problem:** Script doesn't run

**Solutions:**
```bash
# Make executable
chmod +x scripts/prompt-validator.py

# Install Python if needed
python3 --version

# Run with python3 explicitly
python3 scripts/prompt-validator.py "test"
```

---

## Contributing

Have improvements or new templates? 

1. Add to appropriate section
2. Follow existing format
3. Test with validator
4. Update this README

---

## Resources

### Skill Files
- `SKILL.md` - Complete skill guidance
- `templates/` - Ready-to-use templates
- `examples/` - Before/after improvements
- `references/` - Full doctrine + cheat sheet
- `scripts/` - Validation tools

### External Links
- [Anthropic — Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [OpenAI — GPT-5 prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide)
- [Google — Gemini 3 developer guide](https://ai.google.dev/gemini-api/docs/gemini-3) · [Prompt design strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies)
- [PromptingGuide.ai](https://www.promptingguide.ai/)

---

## Success Metrics

Track your improvement:

- [ ] Skill installed and working
- [ ] Used 3+ templates successfully
- [ ] Improved 5+ prompts with doctrine
- [ ] Created custom template for your use case
- [ ] Validated prompts score >75
- [ ] Team members using skill
- [ ] Measurable quality improvement in outputs

---

## FAQ

**Q: Does this work with all LLMs?**
A: Yes. The durable principles apply to GPT-5.x, Claude 4.x, Gemini 3, Llama, etc. The dated 'Current Model Landscape' appendix (doctrine §12) pins vendor-specific behavior you can refresh as models change.

**Q: Do I need the full doctrine file?**
A: No - SKILL.md covers essentials. Reference the full canon for deep dives.

**Q: Can I customize templates?**
A: Absolutely! Templates are starting points - adapt to your needs.

**Q: How often should I validate prompts?**
A: Before deployment, when quality issues arise, or monthly reviews.

**Q: What's the difference from just reading docs?**
A: This skill integrates into your AI assistant, providing contextual help as you work.

---

## License

MIT - Feel free to use, modify, and share.

---

## Changelog

### v2.1 (2026-06)
- New durable section §11 "Embedding Natural Intelligence" — introspective reasoning triggers that turn rule lookups into simulated perspective shifts (be the user / the expert / honest about your own search), with reusable templates for reframing, intent gut-checks, named-failure self-audits, discrimination tests, difficulty calibration, asymmetric-cost defaults, implication inference with restraint, and downstream-usefulness pauses
- Mirrored as a concise section in SKILL.md and the quick-reference; added picker/anti-pattern rows
- Current Model Landscape renumbered §11→§12, Source Guide §12→§13

### v2.0 (2026-06)
- Added Google Gemini 3 throughout; now covers all three frontier vendors
- New "Control Surface" model: reasoning effort / thinking mode / verbosity as parameters
- Chain-of-Thought demoted to a fallback (use the thinking knob instead)
- Assistant prefill marked legacy (rejected with 400 on Claude 4.6+); migration paths added
- Temperature guidance corrected (reasoning models ignore it; Gemini 3 stays at 1.0)
- Long-context ordering fixed (long data at top, query at end)
- New deep section: Agentic systems & context engineering
- New vendor-generic prompt-optimization workflow + 3 new templates (13–15) + 2 new before/after examples (11–12)
- Dated "Current Model Landscape (June 2026)" appendix for Anthropic / OpenAI / Google

### v1.0 (2025-01-30)
- Initial release
- 12 templates
- 10 before/after examples
- Validation script
- Complete doctrine integration

---

*Happy prompting! 🚀*
