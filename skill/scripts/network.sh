#!/usr/bin/env bash
# Thin wrapper around `bsk network` — read buffered network responses/failures
# for a tab. Cursor-paginated: pass the previous call's next_since to --since to
# read only new entries. Keep in sync with network.ps1.

set -euo pipefail

session=""
tab_id=""
since=""
limit=""
max_text_chars=""
json=false

usage() {
  cat <<'EOF'
Usage: network.sh --session SESSION [options]

Options:
  -s, --session SESSION       Session id (must be active) [required]
      --tab-id TAB_ID         Target tab (default: Agent Window active tab)
      --since CURSOR          Return entries with sequence greater than this cursor
      --limit N               Max entries (default 50; extension caps at 200)
      --max-text-chars N      Max chars per URL/error text (default 1000; caps at 4096)
      --json                  Machine-readable JSON output
  -h, --help                  Show this help
EOF
}

while (($#)); do
  case "$1" in
    -s|--session)       session="${2:?missing session}"; shift 2 ;;
    --tab-id)           tab_id="${2:?missing tab-id}"; shift 2 ;;
    --since)            since="${2:?missing since}"; shift 2 ;;
    --limit)            limit="${2:?missing limit}"; shift 2 ;;
    --max-text-chars)   max_text_chars="${2:?missing max-text-chars}"; shift 2 ;;
    --json)             json=true; shift ;;
    -h|--help)          usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -n "$session" ]] || { echo "--session is required" >&2; exit 2; }

args=(bsk network --session "$session")
[[ -n "$tab_id" ]]         && args+=(--tab-id "$tab_id")
[[ -n "$since" ]]          && args+=(--since "$since")
[[ -n "$limit" ]]          && args+=(--limit "$limit")
[[ -n "$max_text_chars" ]] && args+=(--max-text-chars "$max_text_chars")
[[ "$json" == true ]]      && args+=(--json)

"${args[@]}"
