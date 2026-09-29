## Output contract

Return ONLY one JSON object. No prose before or after it, no code fences.

{
  "role": "<your role id>",
  "position": "<your overall stance in 1-2 sentences>",
  "reasoning": ["<up to 3 short points behind the position>"],
  "per_option": [
    {"option": "<option id>", "pros": ["..."], "cons": ["..."], "risks": ["..."]}
  ],
  "surprise": "<one thing the other voices will most likely miss>",
  "confidence": "low | medium | high",
  "evidence": ["<fact from the brief, or concrete mechanism, behind your strongest claim>"]
}

Rules: include exactly one per_option entry for every option in the brief. Stay under 300 words of content. Take your lens all the way; balance is someone else's job.
