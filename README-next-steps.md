
##  Next Steps (Detailed Plan)

This section turns the prototype into an industrial-strength modernization program, preserving semantics while increasing safety, velocity, and auditability.

---

### 1) Enrich the COBOL → IR Parser

**Goal:** move from a minimal structural IR to a *behaviorally rich* model that captures control flow, data flow, and side effects so we can reason about equivalence beyond I/O snapshots.

**Targets to support**

* **Control flow**

  * `PERFORM [THRU]`, `PERFORM VARYING` with exit conditions
  * Nested `IF / EVALUATE` with fall-throughs
  * Declarative sections/paragraph hierarchy
* **Data motion & types**

  * `MOVE`, `COMPUTE`, `ADD/SUBTRACT/MULTIPLY/DIVIDE`
  * Packed/COMP-3, binary, display; USAGE and PICTURE with scaling
  * Redefines, occurs (arrays), renames, level 88 (conditions)
* **I/O**

  * `OPEN/READ/WRITE/REWRITE/CLOSE` + file status handling
  * Declarative error paragraphs (e.g., `USE AFTER ERROR`)
* **Date/time and intrinsic functions**

  * `FUNCTION CURRENT-DATE`, string slicing, reference modification

**IR design direction**

* **Program**: metadata, copybooks, entry points
* **DataModel**: files, records, fields (offset, length, encoding)
* **CFG**: basic blocks with edges; instructions typed (e.g., `Add`, `Compare`, `Move`)
* **Semantics**: symbolic expressions for arithmetic and predicates

**Example (illustrative JSON IR fragment)**

```json
{
  "program": "DAILYPOST",
  "files": [{
    "name": "ACCT-FILE",
    "record": "AccountRec",
    "layout": [
      {"name":"ACCT_ID","kind":"char","len":12,"offset":0},
      {"name":"CURR_BAL","kind":"comp3","digits":13,"scale":2,"offset":29}
    ]
  }],
  "cfg": [{
    "label":"APPLY-TXNS",
    "instructions":[
      {"op":"CompareEq","lhs":"yyyymmdd(TXN_TS)","rhs":20250101},
      {"op":"IfFalse","target":"NEXT-TXN"},
      {"op":"Switch","expr":"TXN_CODE","cases":{
        "DEPO":[{"op":"Add","dst":"CURR_BAL","src":"TXN_AMOUNT"}],
        "WDRW":[
          {"op":"Sub","dst":"TMP_BAL","lhs":"CURR_BAL","rhs":"TXN_AMOUNT"},
          {"op":"CompareGe","lhs":"TMP_BAL","rhs":{"op":"Neg","var":"OD_LIMIT"}},
          {"op":"IfTrue","then":[{"op":"Move","dst":"CURR_BAL","src":"TMP_BAL"}],
           "else":[{"op":"Emit","stream":"EXC-FILE","record":"TXN"}]}
        ]
      }}
    ]
  }]
}
```

**Parser implementation approaches**

* Keep the current stub and incrementally enhance.
* Or adopt/extend a public COBOL grammar (e.g., Koopa, ProLeap) and build visitors that populate your IR (you already know how your record encodings and COMP-3 rules must be modeled).

**Validation strategy**

* Round-trip tests: COBOL → IR → codegen skeleton → hand-written logic
* CFG coverage: assert every paragraph/section is reachable or explicitly suppressed (dead code gates)
* Golden-master parity on growing corpora of real workloads

---

### 2) Expand Alloy Assertions & Model Checking

**Goal:** turn implicit business rules into *executable invariants* you can test against the IR-generated world and real data.

**Core invariants to add**

* **Overdraft bound**
  “Posting must never result in `CURR_BAL < -OD_LIMIT` unless categorised as an exception.”
* **Monotone reconstruction**
  “Resulting balances for day *D* are a pure function of *(opening balance, D-transactions, ruleset)*.”
* **Record consistency**
  All account IDs appearing in postings must exist in the account file (no orphan postings).
* **Idempotence window**
  Re-applying the same day’s postings yields the same state (guards against duplicate ingestion).

**Alloy snippets (illustrative)**

```alloy
sig Account { id: one ID, odLimit: one Int, currBal: one Int }
sig Txn { acct: one Account, code: one Code, amount: one Int, yyyymmdd: one Int }
sig Code {}

one sig DEPO, WDRW, FEE, INT, REV extends Code {}

pred applied(t: Txn, day: Int) { t.yyyymmdd = day }

pred overdraftRespected[a: Account, old: Int, t: Txn] {
  t.code = WDRW implies (old - t.amount) >= -a.odLimit
}

assert NoPostingViolatesOverdraft {
  all a: Account, t: Txn, day: Int |
    applied[t, day] and t.acct = a implies
      overdraftRespected[a, a.currBal, t] or (* diverted to exception stream *)
      t.code != WDRW
}
check NoPostingViolatesOverdraft
```

**Workflow**

* Generate `facts.als` from IR (records, instances from sample data).
* Keep a hand-written `banking.als` with predicates/asserts.
* Use Alloy Analyzer to **check** on sample instances; wire a headless runner in CI for smoke checks.

---

### 3) CI/CD with Golden-Master Equivalence

**Goal:** prevent regressions by verifying **COBOL → modern** parity on every change.

**Recommended pipeline**

1. **Build legacy**: compile COBOL and run `make gm-legacy`.
2. **Run modern**: Kotlin runner (and/or Python runner).
3. **Diff**: `make gm-diff` (CSV-level + SHA-256).
4. **Formal checks (optional gate)**: headless Alloy check.
5. **Artifacts**: store `diff_accounts.csv`, `diff_summary.txt`, and key outputs.

**GitHub Actions (example)**
`.github/workflows/modernization.yml`

```yaml
name: Modernization Golden-Master

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  golden-master:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install GNU COBOL
        run: sudo apt-get update && sudo apt-get install -y open-cobol

      - name: Build COBOL + capture golden master
        run: |
          ./build.sh
          make gm-legacy

      - name: Run Kotlin runner
        run: |
          cd rewrite/kotlin
          ./gradlew --no-daemon run
          cd ../..

      - name: Compare outputs
        run: make gm-diff

      - name: Upload diff artifacts
        uses: actions/upload-artifact@v4
        with:
          name: gm-diff-artifacts
          path: |
            tests/artifacts/diff_summary.txt
            tests/artifacts/diff_accounts.csv
            tests/artifacts/accounts_out_legacy.csv
            tests/artifacts/accounts_out_modern.csv
```

**Data strategy in CI**

* Include a **masked** sample dataset in the repo (already done).
* For private corpora: pull from a secure object store with branch-scoped temp creds; never log raw PII.
* Version large fixtures and pin SHA-256 so unexpected changes fail the build.

---

### 4) Evolve to a Verifiable Microservice (REST or gRPC)

**Goal:** deliver the modernized logic as a service without losing the verifiability you have in batch mode.

**Architecture**

* **Core domain** stays pure and deterministic (no hidden clocks, no global state).
* **Adapters**: I/O (file, DB, message bus), protocol (HTTP/gRPC), observability.
* **Contracts**: define strict request/response schemas; version them.

**Service boundaries**

* **`POST /postings/day`**
  Input: accounts snapshot + transactions for day `D`.
  Output: new account states + exceptions.
  Deterministic: given the same input bytes, output bytes must match **golden master**.

**REST (Ktor) sketch**

```kotlin
routing {
  post("/postings/day") {
    val req = call.receive<PostingRequest>() // accounts + txns (or URIs to blobs)
    val (accounts, exceptions) = domainPost(req)
    call.respond(PostingResponse(accounts, exceptions))
  }
}
```

**gRPC/Protobuf design**

* Prefer gRPC for strong typing and contract-first evolution.
* Use `bytes` fields for **exact** record payloads when you need bit-for-bit reproducibility, and structured messages for higher-level clients.

**Determinism**

* Fix `TODAY` semantics: pass it explicitly; never read system clock inside domain.
* Fix sort orders (stable, total ordering on account ID, timestamp, txn id).
* Fix encodings and decimals; no float/double in domain math (use `Long` cents).

**Observability**

* **Structured logs**: include run ID, dataset digest, counts of applied/exception transactions.
* **Metrics**: applied vs rejected by code (`DEPO/WDRW/FEE/INT/REV`), runtime latency, I/O sizes.
* **Tracing**: attach a correlation ID so a single request’s path is inspectable.

**Migration strategy (strangler pattern)**

1. Mirror production inputs to the service (shadow mode), collect outputs.
2. Compare service outputs with COBOL’s nightly batch (golden-master drift dashboard).
3. Cut over per-product or per-region, with fallbacks.

**Risk controls**

* Contract versioning (e.g., `v1`, `v1.1` with additive fields).
* Back-pressure & idempotency for replays (txn IDs are dedupe keys).
* Canary rollout with feature flags; rollback on non-zero diff rate.

---

### 5) Project Hygiene: Tests, Data, Reproducibility

**Testing layers**

* **Unit**: Money arithmetic, COMP-3 encoding/decoding, sort order, overdraft predicate.
* **Property tests**: random transaction streams—assert invariants and reversible encoding.
* **Fixture tests**: known datasets → expected outputs (CSV + SHA-256).
* **Equivalence tests**: COBOL vs modern as a single test suite.

**Reproducible runs**

* Lock tool versions (JDK 17, Gradle 8.7, cobc version).
* Dockerize for parity across dev/CI/prod.
* Keep `TODAY` an explicit parameter in both batch and service modes.

**Data governance**

* Separate **golden master** corpora from public samples.
* Hash and sign corpora; report digests in logs and CI.
* Create a redaction pipeline (masking) that preserves record sizes when possible (for fixed-width consistency).

---

### 6) Backlog (Concrete Tickets)

* **Parser**

  * [ ] Implement `PERFORM THRU` → CFG edge generation
  * [ ] Parse `EVALUATE` into multi-branch blocks
  * [ ] Map level-88 condition names into boolean guards in IR
  * [ ] Support `REDEFINES`/`OCCURS` → alias analysis in IR

* **Alloy**

  * [ ] Generate instance facts from `data/*.dat` for bounded checks
  * [ ] Add `IdempotentDay` assertion
  * [ ] Add `NoOrphanTxn` assertion (every txn’s account exists)

* **Modern code**

  * [ ] Replace hand-coded fixed-width I/O with generated readers/writers from IR
  * [ ] Introduce a checksum footer per output file (optional control total)
  * [ ] Port Python runner features to Kotlin tests (JUnit)

* **CI/CD**

  * [ ] Add headless Alloy run as non-blocking step (warn on failure)
  * [ ] Publish diff artifacts on PR for reviewer visibility
  * [ ] Add Docker images for local parity

* **Service**

  * [ ] Ktor/gRPC skeleton with explicit `postingDate`
  * [ ] Idempotency via `(acctId, txnId)` index
  * [ ] Golden-master “online diff” endpoint for shadow comparisons

---

By following this plan, you’ll transition from a narrow PoC to a robust modernization platform with **formal guardrails**, **deterministic equivalence checks**, and a **clear path to service-izing** the logic—all while keeping risk near zero.
