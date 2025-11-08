
#  COBOL Modernization Pipeline

### Reverse-Engineering Legacy COBOL into Formal Models and Modern Code

This repository demonstrates a **full modernization pipeline** that converts a legacy **COBOL** system into **formal specifications** and a **modern implementation** (in Kotlin or Python) while preserving byte-level functional equivalence.
The goal is to make legacy mainframe programs *auditable, formally verifiable, and incrementally replaceable*.

Includes scripts and formal spec scaffolding for IR → Alloy → Kotlin transformation.

---

## 🚀 Modernization Goals

Large COBOL codebases often run mission-critical workloads on mainframes, but they suffer from:

* **Obscure business logic** tightly coupled to data layouts.
* **No formal specification** of functionality.
* **High cost of change** due to brittle procedural structure.

This project defines a **structured path** from COBOL to modern systems by introducing a formal and verifiable intermediate layer.

---

## 🧩 High-Level Pipeline

```mermaid
flowchart LR
    A[COBOL Source<br/>DAILYPOST.cbl] --> B[Parser / IR Extractor<br/>make parse]
    B --> C[Formal Model (Alloy)<br/>make alloy]
    B --> D[Code Generator<br/>make gen-kotlin]
    D --> E[Modern Runner (Kotlin/Python)]
    E --> F[Golden Master Comparator<br/>make gm-diff]
    F --> G[Equivalence Proof<br/>Bitwise + Semantic Match]
```

---

## 🧠 Conceptual Overview

### 1️⃣ **COBOL Legacy Layer**

The original COBOL program (`DAILYPOST.cbl`) processes fixed-width binary records (`accounts.dat`, `txns.dat`) to update daily account balances.
It writes out `accounts_out.dat` and `exceptions.dat` using **COMP-3 (packed decimal)** encoding.

This layer represents the **truth source** — the “golden master” for all modernization steps.

---

### 2️⃣ **Intermediate Representation (IR)**

A custom parser (`make parse`) extracts:

* **Record definitions** (`FD`, `01`, `05`, `PIC` clauses)
* **Field lengths and encodings** (ASCII, COMP-3, numeric)
* **Procedural logic flow** (`PERFORM`, `EVALUATE`, etc.)

The result is `parsing/out/ir.json` — a machine-readable abstraction of the COBOL system.

This IR forms the backbone of both formal and modern transformations:

* For **Alloy**, it defines entities and constraints.
* For **Kotlin/Python**, it generates data classes and stub logic.

---

### 3️⃣ **Formal Specification Layer (Alloy)**

The Alloy model (`formal/alloy/facts.als`) formalizes COBOL’s implicit invariants:

* Each `Account` must have ≥ 0 transactions.
* All balances are derived deterministically from inputs.
* Overdrafts are bounded by defined limits.

Using **Alloy Analyzer**, you can explore:

* Structural consistency of records.
* Possible constraint violations.
* Behavioral invariants before and after modernization.

This gives your modernization process **formal assurance** rather than relying on ad-hoc testing.

---

### 4️⃣ **Modern Rewrite Layer (Kotlin)**

The Kotlin rewrite in `rewrite/kotlin/src/main/kotlin/banking/` replaces procedural COBOL with **typed, composable, and testable** logic.

**Key modules:**

* `FixedWidth.kt` — Binary serialization/deserialization matching COBOL’s record structure.
* `Money.kt` — Type-safe fixed-point arithmetic equivalent to COBOL’s COMP-3.
* `Posting.kt` — Business logic equivalent to COBOL’s `DAILYPOST`.
* `ModernRunner.kt` — Entry point for reading input, applying postings, and writing output.

Run it using:

```bash
cd rewrite/kotlin
env -u JAVA_TOOL_OPTIONS ./gradlew run
```

This produces modern output binaries in `out/` and copies them to `tests/artifacts/` for comparison.

---

### 5️⃣ **Golden-Master Validation**

Functional equivalence is proven by running both versions and comparing outputs.

```bash
make gm-legacy   # Run COBOL and capture output
make modern      # Run Kotlin/Python modernization
make gm-diff     # Compare byte-level and CSV-level results
```

The comparator (`scripts/compare_runs.py`) verifies:

* Field-by-field equality.
* Checksums (SHA-256) for full binary identity.
* CSV diffs for human-readable audit logs.

Output example:

```
Compared 2 legacy accounts to 2 modern accounts
Differences: 0
legacy sha256: ac18ac0e6ae5f5a347164be00544e756536b567038f128d3b5b754ea8099f6cf
modern sha256: ac18ac0e6ae5f5a347164be00544e756536b567038f128d3b5b754ea8099f6cf
```

---

## 🧱 Repository Structure

```
cobol-modernization-playbook/
├── cobol/               # Legacy COBOL source
├── data/                # Input fixed-width data files
├── out/                 # COBOL + Kotlin outputs
├── parsing/             # IR extraction artifacts
├── formal/alloy/        # Generated formal specifications
├── rewrite/
│   └── kotlin/          # Modern rewrite
│       ├── build.gradle.kts
│       └── src/main/kotlin/banking/
│           ├── Money.kt
│           ├── FixedWidth.kt
│           ├── Posting.kt
│           └── ModernRunner.kt
├── scripts/             # Python comparator + utilities
├── tests/artifacts/     # Golden master + diff outputs
└── Makefile             # End-to-end automation
```

---

## 🧮 Toolchain

| Component               | Purpose                             | Version              |
| ----------------------- | ----------------------------------- | -------------------- |
| **GNU COBOL** (`cobc`)  | Compile and run legacy source       | 3.1+                 |
| **Python 3**            | Run comparators and scripts         | 3.9+                 |
| **Gradle + Kotlin JVM** | Build and run modern rewrite        | Gradle 8.7 / JDK 17+ |
| **Alloy Analyzer**      | Formal validation of IR constraints | 6.x                  |

---

## ✅ Modernization Principles

| Principle              | Description                                                                     |
| ---------------------- | ------------------------------------------------------------------------------- |
| **Faithful semantics** | Preserve all data encodings and business rules.                                 |
| **Formality**          | Generate verifiable specs before rewriting logic.                               |
| **Incrementality**     | Migrate one module at a time, validating each through golden-master comparison. |
| **Auditability**       | Every modernization step is deterministic and reproducible.                     |
| **Portability**        | Kotlin/Python rewrites can target JVM, native, or cloud runtimes.               |

---

## 🧭 Roadmap

| Stage                          | Description                   | Status     |
| ------------------------------ | ----------------------------- | ---------- |
| COBOL execution & verification | Baseline compiled and working | ✅          |
| IR extraction                  | Structured parse of legacy    | ✅          |
| Formal spec generation         | Alloy + constraints           | 🟩 Ongoing |
| Modern rewrite                 | Kotlin + Python parity        | ✅          |
| Automated equivalence testing  | Golden-master CI              | 🟦 Next    |
| Progressive module replacement | Replace COBOL subsystems      | 🟧 Planned |

---

## 🌐 Why It Matters

* **Regulated industries** need proof that modernization doesn’t alter semantics.
* **Formal specs** serve as living documentation for auditors and engineers alike.
* **Automated equivalence** ensures modernization can proceed confidently, one subsystem at a time.
* **Language neutrality** allows eventual rewrites in Kotlin, Java, Rust, or Python — all verifiable through the same golden-master process.

---
Here’s a section you can append to your main `README.md` under a new heading:

---

## ☕ Java Environment and Diagram Rendering

### Setting up Java for the Kotlin Runner

The modernization runner uses **Kotlin/JVM** and **Gradle**, both of which require Java 17 or later.

If you have multiple JDKs installed (for example Java 8 and 17), explicitly set the environment to use JDK 17 before running Gradle:

```bash
# Point JAVA_HOME to your JDK 17 installation
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"

# Verify
java -version
# → openjdk version "17.0.x"
```

When you run Gradle or the Kotlin runner, remove any legacy options injected by the system (such as `--illegal-access=permit`) to avoid warnings:

```bash
env -u JAVA_TOOL_OPTIONS ./gradlew run
```

This ensures Gradle runs cleanly on Java 17 and avoids conflicts with older Java 8 flags.

---

### 📈 Rendering Diagrams with PlantUML

The repository includes PlantUML diagrams that visualize the full modernization flow.

#### 1️⃣ Install PlantUML

You can either install it system-wide:

```bash
sudo apt update && sudo apt install -y plantuml
```

or download the standalone JAR:

```bash
wget https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar
```

#### 2️⃣ Render the diagrams

From the repository root, run:

```bash
# Render to PNG
plantuml docs/diagram-sequence.puml
plantuml docs/diagram-architecture.puml

# or render to SVG
plantuml -tsvg docs/diagram-sequence.puml
plantuml -tsvg docs/diagram-architecture.puml
```

The generated images (`.png` or `.svg`) will appear in the same `docs/` folder.

#### 3️⃣ Optional: Validate syntax only

```bash
plantuml -checkonly docs/diagram-sequence.puml
plantuml -checkonly docs/diagram-architecture.puml
```

These commands let you confirm the diagrams render correctly and provide clear visual documentation of the entire modernization pipeline.

---


### 📘 Next Steps

* Extend `make parse` to capture more COBOL constructs (`PERFORM THRU`, nested conditionals).
* Add more Alloy assertions (e.g., “balances never go below -overdraft”).
* Integrate CI/CD: run COBOL → Kotlin → diff automatically on every commit.
* Evolve modern logic into a full microservice (REST or gRPC) while maintaining verifiable equivalence.

---

**Author:** Marco Graziano
**Purpose:** Demonstrate a practical, formal, and verifiable path from COBOL to modern, maintainable, and cloud-ready architectures.

---
