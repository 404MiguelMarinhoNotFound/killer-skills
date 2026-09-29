## Output contract

Return ONLY one JSON object: no prose before or after it, no code fences, no comments inside it.

{
  "role": "<your role id>",
  "position": "<your overall stance in 1-2 sentences>",
  "reasoning": ["<1 to 3 short points behind the position, strongest first>"],
  "per_option": [
    {"option": "<option id>", "pros": ["..."], "cons": ["..."], "risks": ["..."]}
  ],
  "surprise": "<one thing the other voices will most likely miss>",
  "confidence": "low | medium | high",
  "evidence": ["<Brief: fact> or <Mechanism: how it happens>, behind your strongest claim>"]
}

How to fill each field:
- `role`: your role id, exactly as given to you.
- `position`: name the option you favour, or the one you would reject, and why in a clause. "It depends" is not a position. If everything truly hinges on one fact, name that fact and give your answer for each value of it.
- `reasoning`: 1 to 3 points, strongest first. One point must say which fact, if it turned out differently, would flip your position.
- `per_option`: exactly one entry for every option id in the brief, written as the brief writes it, the status quo included. Apply the swap test to every pro, con and risk: if the sentence would still be true with another option's name in it, sharpen it or cut it. An empty list is better than filler.
- `surprise`: one concrete point that voices looking through other lenses are likely to overlook. It must add something new, not restate your position.
- `confidence`: `high` when facts in the brief settle it, `medium` when you rely on a reasonable assumption, `low` when it hinges on something the brief does not say.
- `evidence`: 1 to 3 items. Each starts with `Brief:` and restates a fact from the brief, or starts with `Mechanism:` and explains concretely how the effect would come about. Do not cite numbers or studies that are not in the brief.

Stay under 300 words of content. Take your lens all the way; balance is someone else's job.
