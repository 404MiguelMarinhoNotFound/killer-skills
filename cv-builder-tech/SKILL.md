---
name: cv-builder-tech
description: >
  Expert CV building and review skill for Data Engineers, Data Scientists, and AI/ML Engineers
  targeting European tech companies. Use this skill whenever the user asks to write, review,
  improve, tailor, or critique a CV or resume — especially when they mention tech roles, job
  applications, European companies, or say things like "help me with my CV", "review my resume",
  "tailor my CV for this job", "what should I put on my CV", "what do companies look for",
  or "write a CV for a data engineer". Also trigger when the user pastes a job description and
  asks how to match it, or when they share their CV for feedback. This skill provides the full
  doctrine for building a 2026-ready tech CV, grounded in real job postings from top European
  companies like Zalando, Klarna, Siemens, Booking.com, Spotify, and SAP.
---

# CV Builder — Data Engineering · Data Science · AI Engineering
### 2026 Doctrine · European Tech Market Edition

For detailed job posting breakdowns by role, see → `references/job-postings.md`

---

## Core Philosophy

A CV is not a career archive. It is a **targeted argument** answering one question fast:
> *"Why should we hire this specific person for this specific role, right now?"*

Every line must earn its place. Treat it as a marketing document, not a history document.

---

## Format & Structure

**Length**: 1 page (<5 yrs experience) · 2 pages max (senior). Never exceed this.

**Layout**: Reverse chronological. Single or mild two-column. No tables, text boxes, or graphic sidebars — ATS systems choke on them.

**Font**: Calibri, Lato, Roboto, or Ubuntu — 11–12pt body, 14–16pt section headers.

**Margins**: 1 inch all sides. White space is not wasted space.

**Export**: Always PDF. Name it `firstname_lastname_cv.pdf`.

**Section order for tech profiles:**
```
1. Header & Contact
2. Professional Summary
3. Core Skills / Tech Stack
4. Work Experience
5. Projects (optional but high-signal)
6. Education
7. Certifications (optional)
```

---

## Section-by-Section Guide

### 1. Header & Contact
Include: full name (prominent), professional title, city only, professional email, LinkedIn (custom slug), GitHub or personal site, portfolio/notable repos if relevant.

Omit: full address, photo (unless country norm requires it), date of birth, salary.

### 2. Professional Summary (3–4 sentences)
Formula: `[Title]` + `[X years]` + `[core domains]` + `[2–3 specific strengths]` + `[one concrete outcome]` + `[target direction]`

Avoid: "hardworking", "passionate", "dedicated professional", "team player" — zero signal.

### 3. Core Skills / Tech Stack
Group into categories. Never dump a flat list. ATS scans this section for keyword matching.

Example grouping:
```
Languages:        Python, SQL, Scala
Data & Pipelines: Databricks, Apache Spark, Delta Lake, dbt, Airflow
AI / ML:          LangGraph, LangChain, RAG, OpenAI API, Hugging Face, Vector Search
Infrastructure:   AWS, Azure, Docker, Kubernetes, MLflow
Tools:            Git, FastAPI, React
```

Rules: Only list what you can defend in an interview. Explicitly include AI tools — ~41% of 2026 tech postings require AI proficiency. Remove obsolete tools (Hadoop, Python 2).

### 4. Work Experience
Format per role:
```
[Company] — [Title]
[Start] – [End] | [Location]
• Achievement bullet 1
• Achievement bullet 2
```

**The Achievement Rule**: Action verb + what you did + measurable outcome.

| Weak | Strong |
|---|---|
| Worked on data pipelines | Built incremental Silver pipelines in Databricks, reducing data latency from 24h to 15min |
| Used LangChain for RAG | Designed RAG pipeline with Databricks Vector Search, achieving 87% retrieval accuracy |
| Helped deploy models | Deployed LangGraph multi-agent system to production, handling 500+ document queries/day |

**Strong action verbs**: Built · Designed · Deployed · Engineered · Automated · Optimised · Reduced · Integrated · Architected · Shipped · Led · Migrated

**Quantify**: Processing time reduced by X% · latency Xh → Ymin · cost saved €X/month · AUC/F₂ metrics · team size influenced

**Depth**: Last 3–4 roles in full detail. Older/shorter roles: single line. 10+ years ago: drop unless strategically crucial.

### 5. Projects (High-signal for tech roles)
```
[Project Name] — [descriptor]
Tech: [stack used]
• What you built, why, key decisions
• Outcome / status

Links: GitHub / demo / write-up
```

Projects can outweigh job titles for AI/ML roles. Lead with the most relevant to the target role.

### 6. Education
Keep brief. Skills > credentials for tech in 2026. Include thesis title if directly relevant.

### 7. Certifications
Active, recognised only: Databricks Certified · Azure DP-203 · AWS Data Engineer · GCP Professional · Deep Learning Specialisation. Skip expired or irrelevant certs.

---

## ATS Optimisation

~70% of large companies run applications through ATS before any human sees them.

- Mirror exact terminology from the JD (e.g., "MLOps" not "ML Ops")
- Include both acronyms and full forms: `RAG (Retrieval-Augmented Generation)`
- Use standard section headers: `Work Experience`, `Skills`, `Education`
- No critical info in footers or text boxes — ATS skips them
- Target ≥70% keyword match between your CV and the target JD
- Test: copy-paste your PDF into Notepad. If it's garbled, ATS will mangle it

---

## Tailoring per Application

Never submit the same CV twice. Minimum changes per application:
1. Swap summary to target specific company/role
2. Reorder bullets to surface most relevant experience first
3. Adjust skills section language to mirror the JD
4. Lead with the most relevant project

Use Claude to: compare CV against a JD, identify keyword gaps, rephrase bullets. But always rewrite in your own voice — recruiters spot AI-generated CVs immediately.

---

## Design Rules

- Black/dark text on white. Not grey on white.
- Consistent spacing between every section and bullet
- Bullets: use `•` not `→` or `★`
- Never use tables — they break ATS parsers
- No icons, no coloured sidebars (unless creative/design role)
- Test PDF rendering before submitting

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Generic objective statement | Targeted summary with outcomes |
| Responsibilities only | Lead with achievements + metrics |
| One CV for all roles | Tailor per application |
| Flat skills list | Grouped by category |
| Third person ("Miguel is...") | First person implied, no pronoun: "Built..." |
| Salary on CV | Never — that's for negotiation |
| Outdated tools (Hadoop, Python 2) | Remove them |
| File named `resume.pdf` | `firstname_lastname_cv.pdf` |
| Lying or exaggerating | Never — it's fraud and always surfaces |

---

## Cover Letter (When Required)

250–400 words · One page:
1. **Open**: Who you are + one standout achievement + why this role
2. **Middle**: 2–3 specific experiences mapped to the role's requirements
3. **Close**: Why this company specifically. One CTA sentence.

Do not restate your CV. Add personality and context the CV can't convey.

---

## Maintenance

- Review every 6 months even when not job hunting
- Add shipped projects, certs, and tools as they happen — don't reconstruct from memory
- Keep a master CV (all experience) and derive tailored versions from it

---

## Real Job Postings Reference

See `references/job-postings.md` for detailed breakdowns of real postings from:
- **Zalando** (Berlin) — Senior Data Engineer
- **Klarna** (Stockholm/Remote) — Senior Data Engineer
- **Siemens** (Lisbon / Germany) — Senior AI/ML Engineer & AI Engineer
- **Booking.com** (Amsterdam) — Machine Learning Engineer
- **Spotify** (London/Stockholm) — Data Scientist
- **Microsoft AI** — Member of Technical Staff, Data Engineer

Use these to align your CV language and skills to what top European tech companies actually hire for.
