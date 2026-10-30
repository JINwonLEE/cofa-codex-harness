#!/usr/bin/env bash
# Run from the task/project root, not from this kit's checkout.
# Local files only: no network, git commands, or Codex/platform configuration changes.
set -euo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "설치에는 Python 3.8+가 필요합니다. 플랫폼의 허용된 설치 방법을 확인하세요." >&2
  exit 1
fi
exec python3 "$KIT/scripts/install.py" "$@"
