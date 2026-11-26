#!/usr/bin/env bash
set -euo pipefail

RAW_URL="https://raw.githubusercontent.com/777amp/pub-info/main/antigravity/statusline.sh"
AGY_DIR="${HOME}/.gemini/antigravity-cli"
SCRIPT_PATH="${AGY_DIR}/statusline.sh"
SETTINGS_PATH="${AGY_DIR}/settings.json"

mkdir -p "$AGY_DIR"

# 1. Download statusline.sh
echo "Downloading statusline.sh..."
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$RAW_URL" -o "$SCRIPT_PATH"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "$SCRIPT_PATH" "$RAW_URL"
else
  echo "Error: neither curl nor wget is installed." >&2
  exit 1
fi

chmod +x "$SCRIPT_PATH"
echo "Installed: $SCRIPT_PATH"

# 2. Check dependencies
IS_TERMUX=0
if [[ -n "${TERMUX_VERSION:-}" || "${PREFIX:-}" == *"com.termux"* ]]; then
  IS_TERMUX=1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Warning: 'jq' is required for statusline.sh and automatic settings.json updates."
  if (( IS_TERMUX )); then
    echo "  Install with: pkg install jq termux-api"
  else
    echo "  Install with your package manager (e.g., brew install jq / sudo apt install jq)."
  fi
fi

if (( IS_TERMUX )) && ! command -v termux-battery-status >/dev/null 2>&1; then
  echo "Warning: 'termux-battery-status' not found (needed for the battery bar)."
  echo "  Install with: pkg install termux-api (and install the Termux:API companion app)."
fi

# 3. Configure settings.json
if command -v jq >/dev/null 2>&1; then
  if [[ -f "$SETTINGS_PATH" ]] && [[ -s "$SETTINGS_PATH" ]]; then
    TMP_FILE="$(mktemp)"
    if jq '.statusLine = {"type": "command", "command": "bash ~/.gemini/antigravity-cli/statusline.sh"}' "$SETTINGS_PATH" > "$TMP_FILE"; then
      mv "$TMP_FILE" "$SETTINGS_PATH"
      echo "Updated: $SETTINGS_PATH"
    else
      rm -f "$TMP_FILE"
      echo "Error: existing $SETTINGS_PATH is not valid JSON. Please add statusLine manually." >&2
      exit 1
    fi
  else
    cat > "$SETTINGS_PATH" <<'EOF'
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.gemini/antigravity-cli/statusline.sh"
  }
}
EOF
    echo "Created: $SETTINGS_PATH"
  fi
else
  echo ""
  echo "Add this to $SETTINGS_PATH once jq is installed:"
  cat <<'EOF'
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.gemini/antigravity-cli/statusline.sh"
  }
}
EOF
fi

echo "Done. Restart Antigravity CLI (agy) to see the status bar."
