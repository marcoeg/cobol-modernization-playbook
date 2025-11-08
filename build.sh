#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out
echo "Compiling DAILYPOST.cbl with GNU COBOL (cobc)..."
cobc -x -free cobol/DAILYPOST.cbl -I cobol/copybooks -o dailypost
echo "Build complete: ./dailypost"
