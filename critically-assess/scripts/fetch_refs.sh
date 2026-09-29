#!/usr/bin/env bash
# scripts/fetch_refs.sh — download reference skills/prompts into .refs/ (gitignored).
# Read-only inspiration: shipped files must paraphrase, never copy.
set -euo pipefail
REFS_DIR="${REFS_DIR:-.refs}"
SOURCES=(
  "llm-council-remy.md|https://raw.githubusercontent.com/aiwithremy/claude-skills-llm-council/main/SKILL.md"
  "council-ecc.md|https://raw.githubusercontent.com/affaan-m/ECC/main/skills/council/SKILL.md"
  "council-warp.md|https://raw.githubusercontent.com/warpdotdev/common-skills/HEAD/.agents/skills/council/SKILL.md"
  "karpathy-readme.md|https://raw.githubusercontent.com/karpathy/llm-council/master/README.md"
  "karpathy-council.py|https://raw.githubusercontent.com/karpathy/llm-council/master/backend/council.py"
  "anthropic-skill-creator.md|https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md"
)

if [[ "${1:-}" == "--list" ]]; then
  for s in "${SOURCES[@]}"; do echo "${s#*|}"; done
  exit 0
fi

mkdir -p "$REFS_DIR"
: > "$REFS_DIR/SOURCES.md"
for s in "${SOURCES[@]}"; do
  name="${s%%|*}"; url="${s#*|}"
  curl -fsSL "$url" -o "$REFS_DIR/$name"
  sha=$(python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$REFS_DIR/$name")
  echo "- $name | $url | $(date -u +%F) | sha256:$sha" >> "$REFS_DIR/SOURCES.md"
done
echo "Fetched ${#SOURCES[@]} files into $REFS_DIR"
