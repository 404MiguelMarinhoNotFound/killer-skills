# Before/After Prompt Improvements

Real examples of prompts improved using the canon principles.

---

## Example 1: Vague to Specific

### ❌ Before (Score: 3/10)

```
Write something about climate change.
```

**Problems:**
- No task specification
- No audience defined
- No constraints
- No format
- No success criteria

**Typical Result:** Generic essay, unpredictable length, unclear purpose

---

### ✅ After (Score: 9/10)

```
SYSTEM:
You are a science communicator who explains complex topics clearly.

# Goal
Create a 2-paragraph climate change summary for high school students.

# Audience
15-17 year olds with basic science knowledge

# Constraints
- 150-200 words total
- Avoid jargon, or define it
- Include 1 concrete example
- Hopeful tone, not alarmist

# Output Format
## Paragraph 1: The Problem
[What is happening]

## Paragraph 2: What We Can Do
[Solutions and hope]

---

USER:
Topic: Climate change basics

Write the summary following the guidelines above.
```

**Result:** Consistently formatted, appropriate length, accessible language, actionable

---

## Example 2: No Examples to Few-Shot

### ❌ Before (Score: 4/10)

```
Classify the sentiment of customer reviews.

Review: "The product works but setup was confusing."
```

**Problems:**
- No example outputs
- Unclear output format
- No edge case guidance
- No confidence indication

**Typical Result:** Inconsistent format, unclear sentiment scale

---

### ✅ After (Score: 9/10)

```
SYSTEM:
You are a sentiment analysis specialist.

# Task
Classify customer review sentiment and provide confidence score.

# Examples

Input: "This exceeded all my expectations! Amazing quality."
Output: {"sentiment": "positive", "confidence": 0.95, "aspect": "quality"}

Input: "Decent product but shipping took forever."
Output: {"sentiment": "mixed", "confidence": 0.75, "aspect": "service"}

Input: "Completely broken on arrival, waste of money."
Output: {"sentiment": "negative", "confidence": 1.0, "aspect": "quality"}

# Output Format
Valid JSON with:
- sentiment: "positive" | "negative" | "mixed" | "neutral"
- confidence: 0.0-1.0
- aspect: primary topic mentioned

---

USER:
Review: "The product works but setup was confusing."

Classify following the examples above.
```

**Result:** Consistent JSON format, clear sentiment categories, useful confidence

---

## Example 3: Hallucination-Prone to Grounded

### ❌ Before (Score: 2/10)

```
What are the health benefits of turmeric?
```

**Problems:**
- No grounding in sources
- No citation requirement
- No uncertainty handling
- Encourages speculation

**Typical Result:** Mixes facts with unverified claims, no sources

---

### ✅ After (Score: 9/10)

```
SYSTEM:
You are a medical research summarizer who only uses peer-reviewed sources.

# Goal
Summarize research on turmeric's health effects using provided studies.

# Constraints
- Only cite information from <studies>
- Include study reference for each claim
- Distinguish between "shown in studies" vs "theoretical"
- Say "insufficient evidence" when appropriate

# Procedure
1. Extract relevant findings from each study
2. Note the study quality and sample size
3. Identify consensus vs conflicting results
4. Summarize with appropriate caveats

# Output Format
## Findings
- [Claim] [Study reference] [Quality note]

## Limitations
[What the studies don't show]

---

USER:
<studies>
{{RETRIEVED_RESEARCH_PAPERS}}
</studies>

Question: What are the health benefits of turmeric?

Answer using only the provided studies.
```

**Result:** Evidence-based, properly cited, acknowledges limitations

---

## Example 4: Unstructured to Well-Structured

### ❌ Before (Score: 3/10)

```
Analyze this data and tell me what's important.

[Data dump of 500 rows]
```

**Problems:**
- No clear objective
- Overwhelming context
- No guidance on what "important" means
- No output structure

**Typical Result:** Superficial analysis, misses key patterns

---

### ✅ After (Score: 9/10)

```
SYSTEM:
You are a business analyst who finds actionable insights.

# Goal
Identify the top 3 revenue opportunities from sales data.

# Analysis Framework
1. Revenue trends (month-over-month)
2. Customer segment performance
3. Product category gaps
4. Geographic opportunities

# Output Format
## Executive Summary
[2-sentence overview]

## Top 3 Opportunities
### Opportunity 1: [Title]
- Insight: [What the data shows]
- Impact: [Estimated revenue potential]
- Action: [Specific next step]

[Repeat for 2 and 3]

## Supporting Data
[Key metrics table]

---

USER:
<sales_data>
{{FILTERED_500_ROWS}}
</sales_data>

Focus on: Q4 2024 performance
Goal: Find growth opportunities for Q1 2025

Analyze and provide recommendations.
```

**Result:** Focused analysis, actionable insights, clear priorities

---

## Example 5: No Error Handling to Robust

### ❌ Before (Score: 4/10)

```
Extract email and phone from:
"Contact John Doe"
```

**Problems:**
- No handling for missing data
- No validation rules
- No error format
- Assumes data always present

**Typical Result:** Makes up data or fails unpredictably

---

### ✅ After (Score: 10/10)

```
SYSTEM:
You are a data extraction specialist who values accuracy over completeness.

# Goal
Extract contact information from text.

# Rules
- Only extract explicitly stated information
- Use null for missing fields
- Validate email format (contains @)
- Validate phone (digits + optional formatting)
- Never invent or guess data

# Output Format
```json
{
  "email": "string or null",
  "phone": "string or null",
  "confidence": {
    "email": 0.0-1.0,
    "phone": 0.0-1.0
  },
  "errors": ["list of issues if any"]
}
```

# Examples

Input: "Email me at john@example.com or call 555-1234"
Output: {
  "email": "john@example.com",
  "phone": "555-1234",
  "confidence": {"email": 1.0, "phone": 1.0},
  "errors": []
}

Input: "Contact John Doe"
Output: {
  "email": null,
  "phone": null,
  "confidence": {"email": 0.0, "phone": 0.0},
  "errors": ["No email found", "No phone found"]
}

---

USER:
Extract from: "Contact John Doe"

Follow the exact format with validation.
```

**Result:** Handles missing data gracefully, clear error reporting, validated output

---

## Example 6: Wordy to Concise

### ❌ Before (Score: 4/10)

```
You are a very helpful and friendly assistant who always tries 
to be as accurate as possible and provide the best possible 
answers to users. You should be polite and professional at 
all times and make sure to give complete and thorough answers 
that address all aspects of the user's question.

Please analyze the following code and tell me if there are 
any issues with it and what I could do to make it better.
Also, let me know if there are any best practices I should 
be following.

[Code]
```

**Problems:**
- Redundant politeness instructions
- Vague directives ("helpful," "accurate")
- No specific evaluation criteria
- Wall of text, no structure

**Typical Result:** Verbose, unfocused feedback

---

### ✅ After (Score: 9/10)

```
SYSTEM:
You are a code reviewer focused on security and performance.

# Evaluation Criteria
1. Security vulnerabilities
2. Performance bottlenecks
3. Code style violations
4. Error handling gaps

# Output Format
## Critical Issues
[Issues that must be fixed]

## Improvements
[Nice-to-have changes]

## Recommendation
[Overall: Approve / Needs Work / Reject]

---

USER:
<code>
{{CODE}}
</code>

Review following the criteria above. Be specific and concise.
```

**Result:** Focused, actionable, structured feedback

---

## Example 7: Inconsistent Format to Structured Output

### ❌ Before (Score: 5/10)

```
Convert this to JSON:
"Product: Widget, Price: $29.99, Stock: 5"
```

**Problems:**
- No schema specified
- Model may add commentary
- Format not enforced
- Inconsistent responses

**Typical Result:** Sometimes JSON, sometimes explained, sometimes formatted differently

---

### ✅ After (Score: 10/10)

> **2026 update:** The old fix here was assistant *prefill* (`ASSISTANT: {`). That's now **rejected with a 400 error on Claude 4.6+**. Use the vendor's Structured Outputs / strict-schema feature, or an explicit format instruction.

**Preferred — Structured Outputs (works across vendors):**
```
SYSTEM:
Convert the input into JSON. Respond with ONLY valid JSON, no preamble or explanation.

# Schema
{ "product": "string", "price": number, "stock": number }
---
USER:
Input: "Product: Widget, Price: $29.99, Stock: 5"

[Attach the schema via the API's structured-output / strict function-calling mode
 — OpenAI response_format/json_schema, Anthropic tool with input_schema, Gemini responseSchema]
```

**If strict mode is unavailable — explicit instruction (no prefill):**
```
USER:
Convert to JSON matching this schema, output JSON only with no other text:
{ "product": "string", "price": number, "stock": number }
Input: "Product: Widget, Price: $29.99, Stock: 5"
```

**Result:** Guaranteed JSON, no preamble, consistent structure — and no dependency on prefill.

---

## Example 8: Single-Step to Chained

### ❌ Before (Score: 5/10)

```
Read this document and answer questions about it.

Document: [Long legal document]

Questions:
1. What are the payment terms?
2. What are the liability limits?
3. Are there any concerning clauses?
```

**Problems:**
- Single step tries to do too much
- No verification
- Hard to debug if wrong
- Risk of missing details

**Typical Result:** Superficial answers, missed nuances

---

### ✅ After (Score: 9/10)

**Chain 1: Extract**
```
SYSTEM: You are a legal document analyst.

Task: Extract all clauses related to:
- Payment terms
- Liability
- Risk allocation

Output: Exact quotes with section references.

---

<document>
{{LEGAL_DOC}}
</document>

Extract clauses as specified.
```

**Chain 2: Analyze**
```
SYSTEM: You are a contract risk assessor.

Task: Analyze extracted clauses for risks.

<extracted_clauses>
{{CHAIN_1_OUTPUT}}
</extracted_clauses>

For each clause:
1. Summarize in plain language
2. Identify any unusual or concerning terms
3. Rate risk level (low/medium/high)

Output structured analysis.
```

**Chain 3: Summarize**
```
SYSTEM: You are a legal advisor.

<analysis>
{{CHAIN_2_OUTPUT}}
</analysis>

Create executive summary:
- Payment terms (plain language)
- Liability limits
- Top 3 concerns

Format for non-legal audience.
```

**Result:** Thorough, traceable, debuggable, high-quality analysis

---

## Example 9: No Temperature Guidance

### ❌ Before (Score: 6/10)

```
Generate 5 creative product names for a fitness app.
```

**Problems:**
- No temperature specified (defaults vary)
- Inconsistent creativity across runs
- No variation control

**Typical Result:** Unpredictable creativity level

---

### ✅ After (Score: 9/10)

```
SYSTEM:
You are a creative naming specialist.

# Goal
Generate 5 distinctive product names for a fitness app.

# Constraints
- Each name should be unique and memorable
- Avoid clichés (fit, pro, max, etc.)
- 1-2 words maximum
- Easy to pronounce
- Available as .com domain (check common patterns)

# Examples of Good Names
- Strava (original, short)
- Whoop (unique, memorable)
- Peloton (evocative, clear)

# Examples to Avoid
- FitPro, MaxFit, GymMax (generic)

---

USER:
Target audience: 25-35 year olds, tech-savvy
App focus: AI-powered workout planning

Generate 5 names with brief rationale for each.
```

> **2026 update:** The old fix appended `[Set temperature: 0.8]`. On current models that's the wrong lever — reasoning models often ignore/disallow temperature, and **Gemini 3 should stay at its default 1.0** (lowering it can cause loops). For *variety*, the durable technique is to ask the model to propose a wider set and self-select, e.g.: "Generate 12 candidates spanning different naming styles (invented words, compounds, metaphors), then pick the 5 strongest and explain why." This produces more meaningful diversity than a temperature tweak. Reserve temperature tuning for classic non-reasoning completion models.

**Result:** Consistent quality and genuine variety, without depending on a temperature value the model may ignore.

---

## Example 10: Tool Use Without Guardrails

### ❌ Before (Score: 4/10)

```
You can use these tools:
- web_search(query)
- calculator(expression)
- database_query(sql)

User: What's 2+2 and what's the weather?
```

**Problems:**
- No conditional logic
- No error handling
- No user confirmation for risky actions
- May call tools unnecessarily

**Typical Result:** Inefficient tool use, potential errors

---

### ✅ After (Score: 10/10)

```
SYSTEM:
You are a helpful assistant with access to tools.

# Available Tools
- web_search(query) - Search the internet
- calculator(expression) - Evaluate math
- database_query(sql) - Query database [REQUIRES CONFIRMATION]

# Tool Usage Policy
1. Calculator: Use for math (not for "2+2" level simple math)
2. Web Search: Use for current information ONLY
3. Database: ASK user permission first, explain what you'll query

# Procedure
1. Assess if tools are truly needed
2. For risky operations (database), confirm first
3. Explain what you're doing
4. Call tool with validated parameters
5. Handle errors gracefully

# Error Handling
If tool fails:
- Explain what happened
- Offer alternative approach
- Ask if user wants to retry

---

USER:
What's 2+2 and what's the weather?

[Your thoughtful response with appropriate tool use]
```

**Result:** Efficient tool selection, user confirmation for risky actions, clear error handling

---

## Example 11: Over-Engineered to Outcome-First (NEW for 2026)

### ❌ Before (Score: 4/10 on a current model)

```
SYSTEM:
You are an EXPERT analyst. You MUST ALWAYS follow these steps EXACTLY.
CRITICAL: Do not skip any step.
STEP 1: First, you MUST read the entire input carefully.
STEP 2: Then you MUST identify every single relevant fact.
STEP 3: Then you MUST think step by step about each fact.
STEP 4: Then you MUST list pros. STEP 5: Then you MUST list cons.
STEP 6: Then you MUST weigh them. STEP 7: Then you MUST conclude.
You MUST be thorough. You MUST NOT be lazy. NEVER skip steps.
```

**Problems (on Claude 4.x / GPT-5.x / Gemini 3):**
- Heavy process scaffolding narrows the model's search space and produces mechanical output
- "CRITICAL/MUST/ALWAYS/NEVER" intensity now causes over-triggering and rigidity
- "Think step by step" duplicates (and can fight) the model's own thinking mode

**Typical Result:** Stilted, formulaic analysis; ignores better approaches; wasted tokens

---

### ✅ After (Score: 9/10)

```
SYSTEM:
You are a financial analyst.

# Outcome
A decision-useful assessment of whether to proceed with the investment, with the
2–3 factors that most drive the recommendation.

# Constraints
- Ground every claim in the provided data; flag anything you're inferring
- Surface the strongest counterargument, not just supporting points

---
USER:
<data>{{FINANCIALS}}</data>
Based on the information above, give your recommendation.

[reasoning_effort / effort = high; let the model structure its own reasoning]
```

**Why it's better:** States the outcome and constraints, then gets out of the way. Depth comes from the **effort knob**, not a 7-step script. Normal phrasing replaces "CRITICAL/MUST."

---

## Example 12: Manual Chain-of-Thought to the Thinking Knob (NEW for 2026)

### ❌ Before (Score: 5/10 on a reasoning model)

```
Solve this logic puzzle. Let's think step by step. Show every intermediate
step in detail. Think very carefully and don't make mistakes. Reason through
it slowly, step by step, one step at a time, before giving the final answer.
```

**Problems:**
- On a reasoning model, prescribed verbose CoT competes with the model's internal reasoning and can *lower* accuracy
- Forces long visible reasoning you may not want, inflating latency and tokens
- "Think" spam (Claude is literally sensitive to the word when thinking is off)

**Typical Result:** Verbose, sometimes worse reasoning; high latency

---

### ✅ After (Score: 9/10)

**If the model has a thinking mode (preferred):**
```
USER:
Solve this logic puzzle: {{PUZZLE}}
Give the answer, then one short paragraph justifying it.

[effort/reasoning_effort = high; thinking enabled — model reasons internally]
```

**If thinking is OFF (cheap/latency-bound call):**
```
USER:
Solve this logic puzzle: {{PUZZLE}}
Reason it through inside <reasoning> tags, then give the answer in <answer> tags.
Before finishing, verify the answer against the puzzle's constraints.
```

**Why it's better:** Depth is controlled by the parameter, not by begging for steps. Manual CoT becomes a clean, structured fallback only when thinking is unavailable — and the self-verification step (which still helps) is kept.

---

## Key Improvement Patterns

### Pattern 1: Add Structure
- Use delimiters and sections
- Separate instructions from data
- Clear output format

### Pattern 2: Add Examples
- 3-5 representative cases
- Include edge cases
- Show both good and bad examples

### Pattern 3: Add Constraints
- Explicit boundaries
- Error handling rules
- Quality criteria

### Pattern 4: Add Verification
- Citation requirements
- Confidence scores
- Self-checking steps

### Pattern 5: Add Decomposition
- Break complex into steps
- Chain simpler prompts
- Intermediate validation

### Pattern 6: Subtract & Tune (NEW for 2026)
- Delete scaffolding the model doesn't need (process scripts, "MUST/CRITICAL" spam, manual CoT)
- Move "depth" control to the reasoning/effort knob, "length" to verbosity
- Replace negative instructions with positive targets and a single good example

> The first five patterns are about *adding*. On current models, the highest-leverage move is often the sixth: **remove** cruft and **tune the parameters** instead.

---

## Metrics for Measuring Improvement

**Before/After Comparison:**

| Metric | Bad Prompt | Good Prompt |
|--------|-----------|-------------|
| Task success rate | 30-50% | 85-95% |
| Output consistency | Low (high variance) | High (low variance) |
| Hallucination rate | 20-40% | <5% |
| Format compliance | 40-60% | 95%+ |
| User satisfaction | 3/5 | 4.5/5 |
| Debugging time | High | Low |
| Token efficiency | Poor | Good |

---

## Practice Exercise

Try improving these prompts yourself:

1. **Bad:** "Explain machine learning"
   - Add: Audience, depth, format, constraints

2. **Bad:** "Is this email spam? [email text]"
   - Add: Examples, confidence, edge cases

3. **Bad:** "Write code to sort a list"
   - Add: Language, constraints, tests, style guide

Then compare your improvements to the principles in this guide!
