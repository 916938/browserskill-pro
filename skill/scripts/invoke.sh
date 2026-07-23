#!/usr/bin/env bash

# Thin passthrough to `bsk invoke` (or legacy direct commands).
#
# This helper auto-detects whether `bsk invoke` is available:
# - If available (bsk 0.2.0+): forwards raw JSON via `bsk invoke --action <name> --args-json <json>`
# - If unavailable (legacy): falls back to calling typed `bsk <command>` subcommands directly
#
# Historically this helper flattened a JSON args object into `bsk <action>
# --key value` flags on the host side. That required jq (silently dropping
# every argument when jq was missing) and mis-mapped multi-word actions like
# find_tab into non-existent `bsk find tab` commands. The new `bsk invoke`
# command accepts the raw JSON blob and resolves the action to a protocol
# method itself, so in passthrough mode we only validate a few flags and
# forward. Keep it in sync with invoke.ps1.

set -euo pipefail

action=""
session=""
args_json=""
args_json_set=false
args_file=""
output_path=""
timeout=30
dry_run=false
force=false

usage() {
  cat <<'EOF'
Usage: invoke.sh --action ACTION [options]

Options:
  -a, --action ACTION      BrowserSkill tool action (e.g. fill, tab_list, session_stop)
  -s, --session SESSION    BrowserSkill session ID
  -j, --args-json JSON     Action arguments as JSON
  -f, --args-file PATH     UTF-8 JSON file containing action arguments; use - for stdin
      --args-stdin         Read UTF-8 JSON action arguments from stdin
  -o, --output PATH        Save the raw response instead of printing it
  -t, --timeout SECONDS    Request timeout (default: 30)
      --dry-run            Print the bsk command without sending it
      --force              Allow destructive actions such as session_stop
  -h, --help               Show this help

Use --args-file - or --args-stdin for non-ASCII text or complex JSON without a temporary file.

Auto-detection:
  If 'bsk invoke' is available (bsk 0.2.0+), uses passthrough mode.
  Otherwise falls back to legacy direct-command mode.
EOF
}

while (($#)); do
  case "$1" in
    -a|--action)
      action="${2:?missing action}"
      shift 2
      ;;
    -s|--session)
      session="${2:?missing session}"
      shift 2
      ;;
    -j|--args-json)
      args_json="${2:?missing JSON}"
      args_json_set=true
      shift 2
      ;;
    -f|--args-file)
      args_file="${2:?missing file path}"
      shift 2
      ;;
    --args-stdin)
      args_file="-"
      shift
      ;;
    -o|--output)
      output_path="${2:?missing output path}"
      shift 2
      ;;
    -t|--timeout)
      timeout="${2:?missing timeout}"
      shift 2
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    --force)
      force=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ -n "$action" ]] || { echo "--action is required" >&2; exit 2; }
[[ "$action" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "Invalid action name" >&2; exit 2; }

# Session fallback: honor $BSK_DEFAULT_SESSION when --session was not given.
# Explicit --session always wins so agents can override per-call.
if [[ -z "$session" && -n "${BSK_DEFAULT_SESSION:-}" ]]; then
  session="$BSK_DEFAULT_SESSION"
fi

[[ -z "$session" || "$session" =~ ^[A-Za-z0-9_.-]+$ ]] || {
  echo "Session names may contain letters, digits, dot, underscore, and hyphen." >&2
  exit 2
}
[[ "$timeout" =~ ^[1-9][0-9]*$ ]] || { echo "Timeout must be a positive integer." >&2; exit 2; }

if [[ "$args_file" && "$args_json_set" == true ]]; then
  echo "Use either --args-json or --args-file, not both." >&2
  exit 2
fi

# Stopping a session tears down the Agent Window and returns every borrowed
# tab, so guard it behind --force. Cover every spelling the bsk resolver maps
# to session.stop / session.stop_all so --force cannot be bypassed via an
# alternate form (qualified, underscore, or the legacy close_session name).
# Keep this set in sync with invoke.ps1.
case "$action" in
  session_stop|session_stop_all|session.stop|session.stop_all|close_session|tool.session_stop)
    if [[ "$force" != true ]]; then
      echo "Refusing $action without --force; verify every tab is task-owned." >&2
      exit 2
    fi
    echo "Warning: forced $action can close every tab attached to this session. Run tab_list first and verify they are task-owned." >&2
    ;;
esac

# Fail fast instead of blocking on an interactive terminal when stdin is
# requested but nothing is piped in. `bsk invoke` would otherwise wait forever.
if [[ "$args_file" == "-" && -t 0 ]]; then
  echo "Refusing to wait for JSON on an interactive terminal; pipe input or use a heredoc." >&2
  exit 2
fi

# Helper to run Python cross-platform (Windows: py -3 or python, POSIX: python3)
run_python() {
  # Try py (Windows launcher) first
  if command -v py &>/dev/null 2>&1; then
    py -3 "$@"
    return
  fi

  # Try python3 (macOS/Linux standard)
  if command -v python3 &>/dev/null 2>&1; then
    # On Windows, "python3" may redirect to Microsoft Store;
    # verify it's a real Python by checking version
    if python3 --version &>/dev/null 2>&1; then
      python3 "$@"
      return
    fi
  fi

  # Fallback to python (works on Windows with Python installed, and some Linux)
  if command -v python &>/dev/null 2>&1; then
    python "$@"
    return
  fi

  # No Python available
  error "Python not found. Install Python 3.8+ or ensure 'py'/'python'/'python3' is in PATH."
  exit 1
}
# Cache result for performance (within this script invocation).
detect_invoke_support() {
  if bsk invoke --help &>/dev/null 2>&1; then
    return 0  # bsk invoke is available
  else
    return 1  # fall back to legacy mode
  fi
}

# Build the args payload from --args-json or --args-file.
build_args_payload() {
  if [[ "$args_json_set" == true ]]; then
    printf '%s' "$args_json"
  elif [[ -n "$args_file" ]]; then
    if [[ "$args_file" == "-" ]]; then
      cat
    else
      cat "$args_file"
    fi
  else
    printf '{}'
  fi
}

# Execute using bsk invoke (passthrough mode) - preferred for bsk 0.2.0+
execute_with_invoke() {
  local payload
  payload=$(build_args_payload)

  local bsk_args=("bsk" "invoke" "--action" "$action")

  if [[ -n "$session" ]]; then
    bsk_args+=("--session" "$session")
  fi

  # Use --args-json for inline payload or --args-file for file/stdin
  if [[ "$args_json_set" == true ]]; then
    bsk_args+=("--args-json" "$payload")
  elif [[ -n "$args_file" ]]; then
    bsk_args+=("--args-file" "$args_file")
  fi

  bsk_args+=("--timeout-ms" "$((timeout * 1000))" "--json")

  if [[ "$dry_run" == true ]]; then
    # Forward --dry-run to `bsk invoke` so the daemon can validate the action
    # name, JSON schema, and session existence without executing the request.
    # Prints the command first so callers still see what would run.
    bsk_args+=("--dry-run")
    printf '%s\n' "${bsk_args[*]}" >&2
    "${bsk_args[@]}"
    return $?
  fi

  if [[ -n "$output_path" ]]; then
    mkdir -p "$(dirname "$output_path")"
    "${bsk_args[@]}" > "$output_path"
    printf '%s\n' "$output_path"
  else
    "${bsk_args[@]}"
    printf '\n'
  fi
}

# Legacy mode: map action names to specific bsk commands (for bsk < 0.2.0).
# This flattens JSON args into typed flags, which has limitations with
# complex/nested JSON but works for simple cases.
#
# Note: Legacy mode has limited parameter extraction capabilities. For complex
# or nested arguments, upgrade to bsk 0.2.0+ for full passthrough support.
execute_legacy() {
  local cmd=""
  local cmd_args=()

  # Build args payload once for all extractions
  local args_payload
  args_payload=$(build_args_payload)

  # Helper to extract a string value from the JSON payload
  extract_arg() {
    local key="$1"
    local default="${2:-}"
    printf '%s' "$args_payload" | run_python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    result = data.get('$key', '$default')
    if isinstance(result, str):
        print(result)
    else:
        print(result if result is not None else '$default')
except:
    print('$default')
" 2>/dev/null || printf '%s' "$default"
  }

  # Map action names to bsk commands
  case "$action" in
    navigate)
      cmd="navigate"
      cmd_args+=($(extract_arg "url"))
      ;;
    tab_create)
      cmd="tab create"
      local url
      url=$(extract_arg "url")
      if [[ -n "$url" ]]; then
        cmd_args+=("--url" "$url")
      fi
      ;;
    tab_list)
      cmd="tab list"
      local scope
      scope=$(extract_arg "scope")
      if [[ -n "$scope" ]]; then
        cmd_args+=("--scope" "$scope")
      fi
      ;;
    snapshot)
      cmd="snapshot"
      ;;
    click)
      cmd="click"
      cmd_args+=($(extract_arg "selector") $(extract_arg "ref"))
      ;;
    fill)
      cmd="fill"
      local selector value
      selector=$(extract_arg "selector")
      [[ -z "$selector" ]] && selector=$(extract_arg "ref")
      value=$(extract_arg "value")
      cmd_args+=("$selector" "--value" "$value")
      ;;
    evaluate)
      cmd="evaluate"
      cmd_args+=($(extract_arg "expression"))
      ;;
    screenshot)
      cmd="screenshot"
      local ref out
      ref=$(extract_arg "ref")
      out=$(extract_arg "out")
      if [[ -n "$ref" ]]; then
        cmd_args+=("--ref" "$ref")
      fi
      if [[ -n "$out" ]]; then
        cmd_args+=("--out" "$out")
      fi
      ;;
    tab_close)
      cmd="tab close"
      cmd_args+=($(extract_arg "tab_id"))
      ;;
    session_stop)
      cmd="session stop"
      if [[ -n "$session" ]]; then
        cmd_args+=("$session")
      fi
      ;;
    press)
      cmd="press"
      cmd_args+=($(extract_arg "key"))
      ;;
    select)
      cmd="select"
      local ref value
      ref=$(extract_arg "selector")
      [[ -z "$ref" ]] && ref=$(extract_arg "ref")
      value=$(extract_arg "value")
      cmd_args+=("$ref" "--value" "$value")
      ;;
    navigate-back)
      cmd="navigate-back"
      ;;
    navigate-forward)
      cmd="navigate-forward"
      ;;
    reload)
      cmd="reload"
      local hard
      hard=$(extract_arg "hard")
      if [[ "$hard" == "True" || "$hard" == "true" ]]; then
        cmd_args+=("--hard")
      fi
      ;;
    request-help)
      cmd="request-help"
      local prompt title timeout_val
      prompt=$(extract_arg "prompt")
      title=$(extract_arg "title")
      timeout_val=$(extract_arg "timeout" "5m")
      if [[ -n "$prompt" ]]; then
        cmd_args+=("--prompt" "$prompt")
      fi
      if [[ -n "$title" ]]; then
        cmd_args+=("--title" "$title")
      fi
      cmd_args+=("--timeout" "$timeout_val")
      # Extract targets from array
      local targets
      targets=$(printf '%s' "$args_payload" | run_python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    t = data.get('target', [])
    if isinstance(t, str):
        t = [t]
    for item in t:
        print(item)
except:
    pass
" 2>/dev/null || true)
      while IFS= read -r t; do
        [[ -n "$t" ]] && cmd_args+=("--target" "$t")
      done <<< "$targets"
      ;;
    get-html)
      cmd="get-html"
      ;;
    wait-for-navigation)
      cmd="wait-for-navigation"
      ;;
    wait-ms)
      cmd="wait-ms"
      cmd_args+=($(extract_arg "duration"))
      ;;
    tab_select|select-tab)
      cmd="tab select"
      cmd_args+=($(extract_arg "tab_id"))
      ;;
    *)
      echo "Unknown legacy action: $action (bsk invoke unavailable)" >&2
      echo "Available actions: navigate, tab_create, tab_list, snapshot, click, fill, evaluate," >&2
      echo "  screenshot, tab_close, session_stop, press, select, navigate-back," >&2
      echo "  navigate-forward, reload, request-help, get-html, wait-for-navigation," >&2
      echo "  wait-ms, tab_select" >&2
      exit 2
      ;;
  esac

  # Add session flag for commands that require it
  case "$action" in
    navigate|tab_create|snapshot|click|fill|evaluate|screenshot|press|select|\
    reload|get-html|wait-for-navigation|tab_list|tab_close|tab_select)
      if [[ -n "$session" ]]; then
        cmd_args+=("--session" "$session")
      fi
      ;;
  esac

  local bsk_args=("bsk" "$cmd" "${cmd_args[@]}" "--json")

  if [[ "$dry_run" == true ]]; then
    printf '%s\n' "${bsk_args[*]}"
    return 0
  fi

  if [[ -n "$output_path" ]]; then
    mkdir -p "$(dirname "$output_path")"
    "${bsk_args[@]}" > "$output_path"
    printf '%s\n' "$output_path"
  else
    "${bsk_args[@]}"
    printf '\n'
  fi
}

# Main execution logic: auto-detect and dispatch
if detect_invoke_support; then
  execute_with_invoke
else
  execute_legacy
fi
