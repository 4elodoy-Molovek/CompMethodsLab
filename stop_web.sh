#!/usr/bin/env bash
set -euo pipefail

SELF_PID=$$
WORKSPACE="/workspaces/CompMethodsLab"

echo "stop_web.sh starting (pid=$SELF_PID)"

# Avoid running as PID 1 (container init) to prevent accidental shutdown
if [ "$SELF_PID" -eq 1 ]; then
  echo "Running as PID 1 — aborting to avoid killing container init"
  exit 1
fi

# Safe kill helper: send TERM, wait, then KILL remaining
safe_kill() {
  local timeout=${SAFE_KILL_TIMEOUT:-5}
  local targets=()
  for pid in "$@"; do
    [ -z "$pid" ] && continue
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    if [ "$pid" -eq "$SELF_PID" ] || [ "$pid" -eq 1 ]; then
      echo "Skipping PID $pid"
      continue
    fi
    targets+=("$pid")
  done

  if [ ${#targets[@]} -eq 0 ]; then
    return 0
  fi

  echo "Sending SIGTERM to: ${targets[*]}"
  for pid in "${targets[@]}"; do
    kill -TERM "$pid" 2>/dev/null || true
  done

  local end=$((SECONDS + timeout))
  local alive
  while [ $SECONDS -lt $end ]; do
    alive=()
    for pid in "${targets[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then alive+=("$pid"); fi
    done
    if [ ${#alive[@]} -eq 0 ]; then
      echo "All processes exited gracefully."
      return 0
    fi
    sleep 0.5
  done

  echo "Force-killing remaining: ${alive[*]}"
  for pid in "${alive[@]}"; do
    kill -KILL "$pid" 2>/dev/null || true
  done
}

# Stop Node/Electron processes scoped to workspace and main.js
echo "Stopping Node/Electron processes (scoped to $WORKSPACE)..."
mapfile -t NODE_PIDS < <(pgrep -a -f "node" 2>/dev/null | awk -v ws="$WORKSPACE" '$0 ~ ws && $0 ~ /main\.js/ { print $1 }' || true)
safe_kill "${NODE_PIDS[@]}"

# Also consider electron binaries scoped to workspace
mapfile -t NODE_PIDS < <(pgrep -a -f "electron" 2>/dev/null | awk -v ws="$WORKSPACE" '$0 ~ ws { print $1 }' || true)
safe_kill "${NODE_PIDS[@]}"

# Stop Python backend processes scoped to workspace (app.py or flask)
echo "Stopping Python backend (scoped to $WORKSPACE)..."
mapfile -t PY_PIDS < <(pgrep -a -f "python" 2>/dev/null | awk -v ws="$WORKSPACE" '$0 ~ ws && ($0 ~ /app\.py/ || $0 ~ /flask/) { print $1 }' || true)
safe_kill "${PY_PIDS[@]}"

# Fallback: check for any process listening on port 5000
echo "Checking for processes listening on port 5000..."
PORT_PIDS=""
if command -v lsof >/dev/null 2>&1; then
  PORT_PIDS=$(lsof -t -i:5000 || true)
else
  PORT_PIDS=$(ss -ltnp 2>/dev/null | awk -F',' '/:5000/ { if (match($0,/pid=([0-9]+)/,a)) print a[1] }' || true)
fi

if [ -n "$PORT_PIDS" ]; then
  read -r -a PORT_ARR <<<"$PORT_PIDS"
  safe_kill "${PORT_ARR[@]}"
else
  echo "No process found listening on port 5000."
fi

echo "Cleanup complete."
exit 0