#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out
echo "Running dailypost..."
./dailypost || true
echo "Done. Outputs in ./out"
ls -l out || true
