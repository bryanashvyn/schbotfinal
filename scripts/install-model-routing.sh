#!/usr/bin/env bash
# Installs Opus-advisor / Haiku+Sonnet-worker routing into ~/.claude so it
# applies to every repo and every session on this computer.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/.claude"
mkdir -p "$DEST/agents"
cp "$SRC/.claude/agents/haiku-worker.md" "$SRC/.claude/agents/sonnet-worker.md" "$DEST/agents/"

# Merge model settings into ~/.claude/settings.json, keeping existing keys.
python3 - "$DEST/settings.json" <<'PY'
import json, os, sys
p = sys.argv[1]
s = json.load(open(p)) if os.path.exists(p) and os.path.getsize(p) else {}
s["model"] = "opusplan"
s.setdefault("env", {})["CLAUDE_CODE_SUBAGENT_MODEL"] = "sonnet"
json.dump(s, open(p, "w"), indent=2)
PY

# Append routing rules to the global CLAUDE.md once.
touch "$DEST/CLAUDE.md"
if ! grep -q "# Model routing (token saving)" "$DEST/CLAUDE.md"; then
  printf '\n' >> "$DEST/CLAUDE.md"
  cat "$SRC/CLAUDE.md" >> "$DEST/CLAUDE.md"
fi
echo "Installed model routing into $DEST"
