#!/usr/bin/env sh
# Optional anti-pattern lint pass for paperboard-rendered HTML artifacts.
# Uses pbakaus/impeccable's detection rules. Non-blocking by default.
# Exits non-zero on Critical/High findings (CI can gate on this).
#
# Usage:
#   scripts/lint-artifacts.sh                  # lints examples/output/*.html
#   scripts/lint-artifacts.sh path/to/*.html   # lints supplied paths
#   scripts/lint-artifacts.sh path/to/dir      # lints a directory

set -e

if ! command -v npx >/dev/null 2>&1; then
  echo "lint-artifacts: npx not found. Install Node.js to use this optional lint." >&2
  exit 0
fi

if [ "$#" -eq 0 ]; then
  set -- examples/output/*.html
fi

exec npx --no-install impeccable detect "$@"
