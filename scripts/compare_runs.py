#!/usr/bin/env python3
import os, subprocess, sys, hashlib

legacy_bin = "tests/artifacts/accounts_out_legacy.dat"
modern_bin = "tests/artifacts/accounts_out_modern.dat"
out_dir = "tests/artifacts"

def digest(path):
    with open(path, "rb") as f: return hashlib.sha256(f.read()).hexdigest()

if not os.path.exists(legacy_bin):
    print("ERROR: missing", legacy_bin, file=sys.stderr)
    sys.exit(1)

if not os.path.exists(modern_bin):
    print("Modern binary output not found:", modern_bin)
    print("Decoded legacy CSV for inspection will be produced when you run:")
    print("  python3 scripts/decode_accounts.py tests/artifacts/accounts_out_legacy.dat tests/artifacts/accounts_out_legacy.csv")
    print("Tip: once you have modern results, re-run this compare.")
    sys.exit(0)

# If both present, decode and compare
subprocess.check_call([sys.executable, "scripts/compare_accounts.py", legacy_bin, modern_bin, out_dir])

# Also print quick digest equality
print("legacy sha256:", digest(legacy_bin))
print("modern sha256:", digest(modern_bin))
