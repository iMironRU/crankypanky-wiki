#!/usr/bin/env bash
# Дашборд свежести всех карточек (overdue → due_soon → fresh).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 tools/inject_frontmatter.py >/dev/null
echo; sed -n '1,200p' build/freshness-dashboard.md; echo
