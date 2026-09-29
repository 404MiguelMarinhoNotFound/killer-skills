## Output contract

Your reply ends with one JSON object in the shape below, written as plain JSON with no code fences and no comments. Only that final object is read, so everything that matters goes inside it. Use exactly these seven fields and add no others.

{
  "role": "<your role id>",
  "position": "<the option your lens favours or rejects, and why, in 1-2 sentences>",
  "reasoning": ["<1 to 3 points behind the position, strongest first; one starts with Flip:>"],
  "per_option": [
    {"option": "<option id>", "pros": ["..."], "cons": ["..."], "risks": ["..."]}
  ],
  "surprise": "<one point from your lens that the other voices are least likely to raise>",
  "confidence": "low | medium | high",
  "evidence": ["Brief: <a fact the brief states>", "Mechanism: <how the effect comes about>"]
}

How to fill each field:
- `role`: your role id, exactly as given to you.
- `position`: the verdict of your lens alone, not an all-things-considered one. The supervisor combines the lenses, and a voice that drifts toward the middle adds nothing to that mix. Name one option to favour or reject and give the reason in a clause. If the brief leaves a deciding fact open, commit on the reading you find most likely and say which reading you took.
- `reasoning`: 1 to 3 points, strongest first. One point starts with "Flip:" and names the fact that would change your position if it turned out differently. Draw that fact from your own lens, because a flip fact every voice shares tells the supervisor nothing new.
- `per_option`: exactly one entry for every option id in the brief, spelled as the brief spells it, the status quo included. Pros are gains. Cons are costs or drawbacks that come with the option for certain. Risks are things that might go wrong, each with what would set it off. Your role section above says what your lens puts in these lists. Write each item as one sentence and apply the swap test: if the sentence would still be true with another option's name in it, sharpen it or cut it. An empty list is better than filler.
- `surprise`: one concrete point from your lens that voices looking through other lenses are likely to miss. It must add something new, not restate your position or reasoning.
- `confidence`: `high` when facts in the brief settle it, `medium` when you rely on a reasonable assumption, `low` when it hinges on something the brief does not say.
- `evidence`: 1 to 3 items behind your strongest claims. Each starts with `Brief:` and restates a fact the brief gives, or with `Mechanism:` and explains step by step how the effect would come about. Cite numbers, prices or studies only if the brief contains them. A gap in the brief is not evidence: name the gap in `reasoning` and let it lower `confidence`. Prefer the facts that matter most to your lens; a fact every voice would cite adds little.

Keep the whole object to about 300 words; one sentence per list item is enough. Take your lens all the way. The Analyst supplies the balance, so you do not have to.
