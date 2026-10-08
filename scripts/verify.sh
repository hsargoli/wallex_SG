#!/usr/bin/env bash
# verify.sh — Wallex health check (reproducible witness)
# Usage: cd ~/wallex && bash scripts/verify.sh

set -u
cd "$(dirname "$0")/.." || exit 1

echo "=== git ==="
git status --short | head -10
git log --oneline -5
echo "branch: $(git branch --show-current)"

echo ""
echo "=== tests ==="
cd backend && (uv run pytest -q 2>&1 | tail -3); cd ..

echo ""
echo "=== docs ==="
ls docs/

echo ""
echo "=== endpoints ==="
grep -rhE "@router\.(get|post|put|delete|patch)" \
  backend/app/presentation --include=*.py | wc -l

echo ""
echo "=== pages ==="
find frontend/app -name page.tsx | wc -l

echo ""
echo "=== bots ==="
ls -d backend/app/services/bots/*/ 2>/dev/null \
  | grep -v __pycache__ | wc -l

echo ""
echo "=== live trading ==="
curl -s localhost:8000/v1/orders/trading-mode; echo
curl -s localhost:8000/health; echo

echo ""
echo "=== frontend tsc ==="
cd frontend && (npx tsc --noEmit 2>&1 | grep -c "error TS"); cd ..

echo ""
echo "=== done ==="
