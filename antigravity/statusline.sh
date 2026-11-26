#!/usr/bin/env bash
set -uo pipefail

# Read JSON payload piped by Antigravity CLI
PAYLOAD="$(cat)"

# ANSI colors
RESET=$'\033[0m'
DIM=$'\033[2m'
CYAN=$'\033[36m'
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'

color_for_pct() {
  local pct="$1"
  if (( pct >= 50 )); then
    printf '%s' "$GREEN"
  elif (( pct >= 20 )); then
    printf '%s' "$YELLOW"
  else
    printf '%s' "$RED"
  fi
}

fmt_reset() {
  local sec="${1:-0}"
  if (( sec <= 0 )); then return; fi
  local d=$(( sec / 86400 ))
  local h=$(( (sec % 86400) / 3600 ))
  local m=$(( (sec % 3600) / 60 ))
  if (( d > 0 )); then
    printf ' (%dd%dh)' "$d" "$h"
  elif (( h > 0 )); then
    printf ' (%dh%dm)' "$h" "$m"
  else
    printf ' (%dm)' "$m"
  fi
}

# --- LINE 1: Model & Quota ---
MODEL="$(jq -r '.model.display_name // .model.id // "unknown"' <<< "$PAYLOAD" 2>/dev/null || echo "unknown")"

# Pick quota buckets matching the active model (Argon -> Gemini -> 3rd-party -> fallback)
QUOTA_LINES="$(jq -r --arg m "$(tr '[:upper:]' '[:lower:]' <<< "$MODEL")" '
  (.quota // {}) as $q |
  (if ($m | contains("argon")) then
      ["gemini-argon-wtu-weekly"]
   elif ($m | contains("gemini")) then
      ["gemini-5h", "gemini-weekly"]
   else
      ["3p-5h", "3p-weekly"]
   end) as $preferred |
  ($preferred | map(select($q[.] != null and ($q[.].disabled // false) == false))) as $matched |
  (if ($matched | length) > 0 then $matched
   else ($q | to_entries | map(select((.value.disabled // false) == false) | .key))
   end)[] |
  . as $k | $q[$k] |
  select(.remaining_fraction != null) |
  [
    (if ($k | contains("5h")) then "5h"
     elif ($k | contains("weekly")) then "7d"
     else $k end),
    ((.remaining_fraction * 100) | round),
    (.reset_in_seconds // 0 | floor)
  ] | @tsv
' <<< "$PAYLOAD" 2>/dev/null)"

QUOTA_OUT=""
if [[ -n "$QUOTA_LINES" ]]; then
  while IFS=$'\t' read -r label pct reset_sec; do
    [[ -z "$label" ]] && continue
    c="$(color_for_pct "$pct")"
    r="$(fmt_reset "$reset_sec")"
    [[ -n "$QUOTA_OUT" ]] && QUOTA_OUT+=" ${DIM}|${RESET} "
    QUOTA_OUT+="${label}: ${c}${pct}%${RESET}${DIM}${r}${RESET}"
  done <<< "$QUOTA_LINES"
else
  QUOTA_OUT="${DIM}Quota: --${RESET}"
fi

printf '%s%s%s %s|%s %s\n' "$CYAN" "$MODEL" "$RESET" "$DIM" "$RESET" "$QUOTA_OUT"

# --- LINE 2: Termux Device Battery (only rendered on Termux) ---
if [[ -n "${TERMUX_VERSION:-}" || "${PREFIX:-}" == *"com.termux"* ]] && command -v termux-battery-status >/dev/null 2>&1; then
  CACHE_FILE="${TMPDIR:-/tmp}/agy-termux-battery.cache"
  CACHE_TTL=30
  NOW="$(date +%s)"

  CACHED_TS=0
  BAT_PCT=""
  BAT_STATUS=""

  if [[ -f "$CACHE_FILE" ]]; then
    read -r CACHED_TS BAT_PCT BAT_STATUS < "$CACHE_FILE" 2>/dev/null || true
  fi

  if (( NOW - CACHED_TS >= CACHE_TTL )) || [[ -z "$BAT_PCT" ]]; then
    RAW_BAT="$(timeout 2 termux-battery-status 2>/dev/null || true)"
    if [[ -n "$RAW_BAT" ]]; then
      NEW_PCT="$(jq -r '.percentage // empty' <<< "$RAW_BAT" 2>/dev/null || true)"
      NEW_STATUS="$(jq -r '.status // "UNKNOWN"' <<< "$RAW_BAT" 2>/dev/null || true)"
      if [[ -n "$NEW_PCT" ]]; then
        BAT_PCT="$NEW_PCT"
        BAT_STATUS="$NEW_STATUS"
        printf '%s %s %s\n' "$NOW" "$BAT_PCT" "$BAT_STATUS" > "$CACHE_FILE" 2>/dev/null || true
      fi
    fi
  fi

  if [[ -n "$BAT_PCT" ]]; then
    bc="$(color_for_pct "$BAT_PCT")"
    case "$BAT_STATUS" in
      CHARGING) tag="⚡ charging" ;;
      FULL)     tag="✓ full" ;;
      *)        tag="" ;;
    esac
    if [[ -n "$tag" ]]; then
      printf 'Battery: %s%s%%%s %s(%s)%s\n' "$bc" "$BAT_PCT" "$RESET" "$DIM" "$tag" "$RESET"
    else
      printf 'Battery: %s%s%%%s\n' "$bc" "$BAT_PCT" "$RESET"
    fi
  else
    printf '%sBattery: N/A%s\n' "$DIM" "$RESET"
  fi
fi
