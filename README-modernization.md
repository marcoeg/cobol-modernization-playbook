# COBOL Modernization Suite — End-to-End (Legacy ⇄ Modern)

This repository contains a **working mainframe slice** (COBOL daily posting) **plus a modernization pipeline** to help you **reverse-engineer, specify, and rewrite** the system safely—*without losing behavior*. You can shadow-run a modern implementation against the legacy executable and compare results automatically.

## Why modernization? (Purpose)

- **Legacy risk:** knowledge is locked in COBOL; onboarding is slow; delivery cadence is limited.
- **Spec drift:** decades of patches create implicit rules that aren’t documented.
- **Safety:** rewriting without a reference invites regressions. We want *provable equivalence*.
- **Goal:** extract a **formal-ish IR**, check invariants, and generate a **modern implementation** that matches legacy outputs on real data. Cut over with confidence (strangler pattern).

---

## What’s inside

```
cobol/                      # GNU COBOL program + copybooks
data/                       # fixed-width inputs (binary; COMP-3 for amounts)
out/                        # runtime outputs (legacy & modern)
scripts/
  parse_stub.py             # COBOL→IR placeholder (replace with real parser later)
  ir_schema.json            # IR schema (doc + validation target)
  ir_to_alloy.py            # IR→Alloy (emits facts)
  ir_to_kotlin.py           # IR→Kotlin domain skeleton
  modern_runner.py          # NEW: Python modern implementation (reference)
  run_golden_master.sh      # runs legacy cobol binary and captures outputs
  decode_accounts.py        # COMP-3 decoder (accounts) → CSV
  compare_accounts.py       # legacy vs modern CSV diff
  compare_runs.py           # orchestrates comparison and prints digests
formal/
  alloy/
    banking.als             # base Alloy model (handwritten invariants)
    facts.als               # generated facts from IR
Makefile                    # pipeline driver (make parse/alloy/gen-kotlin/gm-legacy/gm-diff)
build.sh, run.sh            # build/run COBOL binary
```

---

## Quick start

### 0) Build the legacy COBOL
```bash
./build.sh
./run.sh   # optional smoke test
```

### 1) Generate IR + Alloy + Kotlin stubs
```bash
make parse
make alloy
make gen-kotlin
```

### 2) Capture the golden master from COBOL
```bash
make gm-legacy
# writes tests/artifacts/accounts_out_legacy.dat (+ CSV decode)
```

### 3) Run the modern (Python) implementation
```bash
python3 scripts/modern_runner.py
# writes out/accounts_out_modern.dat and tests/artifacts/accounts_out_modern.dat
```

### 4) Compare legacy vs modern
```bash
make gm-diff
# outputs tests/artifacts/diff_summary.txt and diff_accounts.csv
```

If `MATCH`, your modern code replicates the legacy behavior on this dataset.

---

## How the Python modern runner works

**File formats**  
- `data/accounts.dat` — 58 bytes/record:
  - 0–11: ACCT_ID (X(12))
  - 12–23: CUST_ID (X(12))
  - 24–27: PRODUCT (X(4))
  - 28:    STATUS (X(1))
  - 29–35: CURR_BAL (S9(11)V99 COMP-3) → **13 digits** incl 2 decimals
  - 36–41: OD_LIMIT (S9(9)V99 COMP-3)  → **11 digits** incl 2 decimals
  - 42–49: OPEN_DATE (YYYYMMDD)
  - 50–57: CLOSE_DATE (YYYYMMDD)
- `data/txns.dat` — 72 bytes/record:
  - 0–11:  ACCT_ID (X(12))
  - 12–27: TXN_ID (X(16))
  - 28–43: ORIG_ID (X(16))
  - 44–47: CODE (X(4)) — `DEPO`, `WDRW`, `FEE `, `INT `, `REV `
  - 48–53: AMOUNT (S9(9)V99 COMP-3) → **11 digits** incl 2 decimals
  - 54–67: TS (YYYYMMDDHHMMSS)
  - 68–71: CHANNEL (X(4))

**Business rules (mirrors COBOL):**
- Only transactions with **TS(1:8) == TODAY** (hard-coded as `20250101`) are applied.
- `DEPO`, `FEE `, `INT ` → add amount to balance.
- `REV ` → subtract amount.
- `WDRW` → apply **only if** `newBal >= -OD_LIMIT`; otherwise **exception**.

**Outputs:**
- `out/accounts_out_modern.dat` — exact same 58-byte layout and COMP-3 packing.
- `out/exceptions_modern.dat` — same 72-byte layout as input txns.
- `tests/artifacts/accounts_out_modern.dat` — copy for comparator.

---

## The IR + Formal angle (why we do this)

- **IR**: a language-neutral model of records/operations (types, enums, invariants).  
- **Alloy model**: check invariants like “active accounts never go below negative overdraft.”  
- **Kotlin skeleton**: a target for a statically-typed rewrite (service/back-end).

This gives you a *safety net*: the legacy binary becomes the oracle, IR captures intent, Alloy asserts properties, and codegen avoids drift.

---

## LLMs: where they help (and where they don’t)

- ✅ extracting enums/domains from copybooks; proposing invariants/guards as English → IR
- ✅ generating unit tests and edge-case vectors; explaining diffs
- ✅ drafting human docs from code slices (you still review)
- ❌ not a replacement for the comparator or formal checks

Always bind LLM suggestions back to **IR + Alloy + golden-master diffs**.

---

## Roadmap to a full rewrite

1. Replace `scripts/parse_stub.py` w/ a real grammar-driven parser (Koopa/ProLeap + custom visitors).
2. Expand IR to cover more files, joins, date cutovers, end-of-month logic, etc.
3. Generate **readers/writers** from IR (no hand-coded fixed-width glue).
4. Flesh out Kotlin/Java service with persistence, APIs, and observability.
5. Shadow-run in production (strangler), diff on mirrored datasets.
6. Cut over once diffs are exhausted and invariants hold on real data volumes.

---

## Troubleshooting

- **Comparator says different** → Inspect `tests/artifacts/diff_accounts.csv`. Use `scripts/decode_accounts.py` to spot balance differences.
- **Record length error** → Ensure your inputs are the expected sizes: 58 bytes (accounts), 72 bytes (txns).
- **Today filter** → Runner and COBOL both use `20250101`. Align if you change either.

---

