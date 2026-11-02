#!/usr/bin/env bash
# Rebuild docs/sample-report.md and docs/sample-briefing.html from recorded replies.
# No API spend; uses .venv when present, otherwise $PYTHON.
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"

port=${PORT:-8791}
home=$(mktemp -d)
model="deepseek/deepseek-v4.1-flash-1017"
base="http://127.0.0.1:$port/v1"
py=${PYTHON:-python}
if [ -z "${VIRTUAL_ENV:-}" ] && [ -x .venv/bin/python ]; then
  py=.venv/bin/python
fi

"$py" scripts/stub_endpoint.py --port "$port" &
stub=$!
trap 'kill "$stub" 2>/dev/null; rm -rf "$home"' EXIT
sleep 1

SCAMSCRIPT_HOME="$home" "$py" -m scamscript --api-key stub --base-url "$base" \
  --model "$model" --redact batch examples --output docs/sample-report.md --force

run=$(basename "$(ls "$home/logs"/*.jsonl | head -1)" .jsonl)
SCAMSCRIPT_HOME="$home" "$py" -m scamscript --api-key stub --base-url "$base" \
  --model "$model" brief --run-id "$run" --logs-dir "$home/logs" --html \
  --output docs/sample-briefing.html --force

sed -i "s|$root/||g" docs/sample-report.md
echo "rebuilt docs/sample-report.md and docs/sample-briefing.html from run $run"
