#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR/backend"
python -m compileall -q .
PYTHONPATH=. pytest -q

cd "$ROOT_DIR/frontend"
npm run build

echo "Smart Pantry release validation passed."
