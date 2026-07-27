#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
cd "$root"

if [[ -x "$root/.venv/bin/python" ]]; then
  exec "$root/.venv/bin/python" "$root/src/init.py" "$@"
fi
exec python3 "$root/src/init.py" "$@"
