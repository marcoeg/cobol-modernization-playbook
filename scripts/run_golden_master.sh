#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf out && mkdir -p out
./dailypost
cp -f out/accounts_out.dat tests/artifacts/accounts_out_legacy.dat
cp -f out/exceptions.dat   tests/artifacts/exceptions_legacy.dat
echo "Captured legacy outputs in tests/artifacts/"

# decode legacy for convenience
python3 scripts/decode_accounts.py tests/artifacts/accounts_out_legacy.dat tests/artifacts/accounts_out_legacy.csv || true
