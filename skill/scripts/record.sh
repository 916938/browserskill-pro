#!/usr/bin/env bash
# Thin wrapper around `bsk record start` / `bsk record stop`.
# Blocks until the user clicks Finish in the recording panel, then prints
# the trace file path. Keep in sync with record.ps1.

set -euo pipefail

subcmd=""
browser=""
url=""
purpose=""
output="trace.json"

usage() {
  cat <<'EOF'
Usage: record.sh start|stop [options]

  start   Open Agent Window, start recording, block until Finish clicked.
  stop    Terminal fallback to stop recording when browser panel unavailable.

Options (start only):
  -b, --browser INSTANCE   Browser instance id or label (multi-browser setups)
  -u, --url URL            Initial URL (default: https://example.com/)
  -p, --purpose TEXT       Optional context metadata for the trace
  -o, --output PATH        Trace output file (default: trace.json)
  -h, --help               Show this help

Options (stop only):
  -o, --output PATH        Trace output file (default: trace.json)
EOF
}

[[ $# -gt 0 ]] || { usage >&2; exit 2; }
case "$1" in
  -h|--help) usage; exit 0 ;;
esac
subcmd="$1"; shift

while (($#)); do
  case "$1" in
    -b|--browser) browser="${2:?missing browser}"; shift 2 ;;
    -u|--url)     url="${2:?missing url}"; shift 2 ;;
    -p|--purpose) purpose="${2:?missing purpose}"; shift 2 ;;
    -o|--output)  output="${2:?missing output}"; shift 2 ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$subcmd" in
  start)
    args=(bsk record start --output "$output")
    [[ -n "$browser" ]] && args+=(--browser "$browser")
    [[ -n "$url" ]]     && args+=(--url "$url")
    [[ -n "$purpose" ]] && args+=(--purpose "$purpose")
    "${args[@]}"
    echo "$output"
    ;;
  stop)
    bsk record stop --output "$output"
    echo "$output"
    ;;
  *)
    echo "Unknown subcommand: $subcmd (expected start or stop)" >&2
    usage >&2
    exit 2
    ;;
esac
