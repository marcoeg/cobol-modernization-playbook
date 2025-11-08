# Reverse Engineering Large COBOL Systems into Formal Models

When facing a very large COBOL codebase, the priority is not immediate translation, but durable understanding.
The goal is to build a scalable Intermediate Representation (IR) that captures structure, data, and behavior —
and then project it into one or more formal or specification languages such as **Alloy**, **TLA+**, or **SMT** for verifiable modernization.

---

## 1. Define the Modernization Objective

Before extracting or converting any code:

- Identify key business capabilities (e.g., posting, interest accrual, reconciliation).
- Define invariants that must hold: control totals, balances, regulatory reports, or replay idempotence.
- Select equivalence oracles (golden-master outputs) that will serve as truth during modernization.

---

## 2. Build a Layered Intermediate Representation (IR)

Design an extensible IR you own and evolve. Each layer adds understanding without rewriting code.

| Layer | Description |
|--------|--------------|
| **Syntactic IR (AST)** | Tokens, paragraphs, sections, `PERFORM` targets, copybook expansions |
| **Structural IR (Data/Layout)** | File definitions, record structures, offsets, COMP-3 encodings |
| **Control-Flow IR (CFG)** | Basic blocks, edges, `EVALUATE` branches, `PERFORM THRU` ranges |
| **Effects IR (R/W Sets)** | Tracks which records, files, or fields each block reads or writes |
| **Semantic IR (Predicates/Algebra)** | Normalized algebra of domain rules, e.g., posting = add/sub with guards |

This layered IR allows partial progress: even without semantics, structure and flow already reveal dependencies and modernization impact.

---

## 3. System Graph Indexing

Represent the system as a **graph**:

- **Nodes:** programs, paragraphs, copybooks, datasets, JCL steps.  
- **Edges:** CALL, PERFORM, READ, WRITE, INCLUDE, REDEFINE.  
- **Queries:** “Which modules write file X?”, “What fields influence balance computation?”, “Which programs use copybook Y?”

This makes it possible to analyze complexity, detect dead code, and define *strangler slices* for incremental replacement.

---

## 4. Establish Golden-Master Harnesses

For each high-value job:

1. Capture repeatable runs with pinned input datasets.  
2. Persist output files and control totals.  
3. Compute and store SHA-256 hashes for reproducibility.  

These become **behavioral oracles** — the standard to which every rewritten or refactored component is compared.

---

## 5. Formalize Key Invariants

Use formal languages to prove what matters most:

| Type | Example Invariant | Tool |
|------|--------------------|------|
| Data Integrity | Every Transaction must belong to an existing Account | Alloy |
| Business Rule | balanceAfterWithdrawal ≥ -overdraftLimit | Alloy / Z3 |
| Temporal | Nightly batch replay is idempotent | TLA+ |
| Arithmetic | Interest accrual never exceeds regulatory cap | SMT (Z3) |

Formalization lets you verify *all possible states within scope*, not just tested cases.

---

## 6. Behavioral Slicing

Divide the codebase into **business slices** — minimal, self-contained units such as posting or fees.

For each slice:
- Extract its I/O contracts (files, copybooks, records).  
- Capture semantic rules (guards, computations).  
- Generate formal specifications (Alloy facts or TLA+ models).  
- Validate against golden-master outputs.

This allows modular modernization while maintaining correctness.

---

## 7. Toolchain Options

**COBOL Parsing and IR Extraction**
- [ProLeap COBOL Parser](https://github.com/uwol/proleap-cobol-parser)
- [Koopa COBOL Toolkit](https://github.com/abaplint/koopa)
- [cb2xml](https://sourceforge.net/projects/cb2xml/) for copybook-to-XML conversion

**Formal Modeling**
- [Alloy](https://alloytools.org/) — structural and relational invariants  
- [TLA+](https://lamport.azurewebsites.net/tla/tla.html) — temporal and scheduling reasoning  
- [Z3 SMT Solver](https://github.com/Z3Prover/z3) — arithmetic and logical proof checking

**Storage and Visualization**
- JSON for interchange, Parquet for large-scale analytics  
- Neo4j or Graphviz for visualizing call and data dependencies  
- PlantUML for pipeline and model diagrams  

---

## 8. Role of LLMs

LLMs can **accelerate** understanding — not replace verification.

✅ *Good uses:*
- Summarize COBOL paragraphs and JCL job flows  
- Suggest candidate invariants or data models  
- Cluster similar programs (using embeddings)  

⚠️ *Avoid using for:*
- COMP-3 decoding, byte-level layout inference, or arithmetic semantics  
- Final transformations without verification  

Always treat LLM suggestions as **inputs to the formal pipeline**, never as authoritative sources.

---

## 9. 90-Day Incremental Plan

### Phase 1 – Inventory & IR v1 (Weeks 1–3)
- Parse copybooks → canonical record catalog.  
- Build **Syntactic + Structural IR** for top 10 jobs.  
- Populate the system **graph index**.

### Phase 2 – CFG & Effects (Weeks 3–6)
- Expand control-flow and read/write sets.  
- Extract job-level **I/O contracts** and **control totals**.  
- Capture golden-master runs for verification.

### Phase 3 – Formalization (Weeks 6–8)
- Generate **Alloy facts** and add core invariants.  
- Model nightly batch workflow in **TLA+**.

### Phase 4 – Behavioral Slices & Modern Rewrites (Weeks 8–12)
- Select 2–3 slices for pilot modernization.  
- Define **semantic IR** (rules and guards).  
- Validate equivalence with golden-master outputs.

### Phase 5 – CI/CD Governance (Ongoing)
- Automate COBOL → IR → Alloy → Modern runner → Diff on every commit.  
- Gate deployments on formal verification and equivalence reports.  
- Monitor drift between legacy and modern systems.

---

## 10. Summary

Reverse-engineering a legacy COBOL system at scale requires **discipline, structure, and formalism**.  
The process is not about line-by-line conversion — it’s about **reconstructing verifiable semantics**.

- Build a layered IR.  
- Formalize invariants using Alloy, TLA+, or Z3.  
- Use golden-master diffs to guarantee behavioral parity.  
- Modernize in slices, not all at once.  
- Integrate everything into CI/CD for continuous semantic verification.

This strategy transforms modernization from a risky translation task into a **provable, iterative reconstruction** — with every step grounded in data, logic, and evidence.

---

## 🧩 Formal Specification Languages for Modernization

As part of the modernization pipeline, your IR (Intermediate Representation) can be projected into formal specification languages.  
These languages let you verify invariants, model concurrency and temporal behavior, and prove properties about both the legacy system and its modern equivalents.

Below is an overview of the main languages recommended in this framework:

### ⚙️ [Alloy](https://alloytools.org/)
Alloy is a **declarative relational modeling language** and comes with the [Alloy Analyzer](https://alloytools.org/documentation/).  
It models static structures and data relationships, exploring all possible configurations within a scope to find counterexamples.

**Why Alloy:** ideal for COBOL’s record-oriented structures, proving relational invariants like “every transaction has a matching account.”

### ⏱ [TLA+](https://lamport.azurewebsites.net/tla/tla.html)
TLA+ (Temporal Logic of Actions) describes systems as state transitions. It’s great for modeling **batch processes**, **workflow sequencing**, and **idempotence** checks.  
The [TLA+ Toolbox](https://lamport.azurewebsites.net/tla/toolbox.html) provides model checking and counterexample exploration.

**Why TLA+:** COBOL job chains and nightly batches have complex temporal semantics; TLA+ proves ordering and safety properties.

### 🧮 [SMT and Z3](https://github.com/Z3Prover/z3)
SMT (Satisfiability Modulo Theories) solvers like **Z3** check arithmetic, logical, and symbolic constraints.  
They prove whether numeric invariants hold under all inputs — perfect for balance, limit, and interest logic validation.

**Why SMT:** COBOL arithmetic (COMP-3, fixed-point) can be mapped to integer constraints; Z3 can prove these transformations are correct.

### 🔗 Comparative Summary

| Language | Focus | Best For | Tooling | Complementarity |
|-----------|--------|----------|----------|----------------|
| **Alloy** | Structural / relational | Schema integrity, record relationships | Alloy Analyzer | Great for data consistency |
| **TLA+** | Temporal logic | Workflow order, liveness, batch flow | TLA+ Toolbox | Great for temporal correctness |
| **SMT / Z3** | Symbolic logic | Numeric and arithmetic constraints | Z3 Solver | Great for arithmetic verification |

---

### 🧠 Integration into the Modernization Pipeline

1. **COBOL → IR (JSON)** — structural and behavioral facts extracted.  
2. **IR → Alloy** — static invariants checked (data correctness).  
3. **IR → TLA+** — temporal semantics verified (workflow correctness).  
4. **IR → SMT** — arithmetic constraints validated (calculation correctness).  
5. **Modern Code → Comparator** — equivalence tested against golden-master outputs.

Together, these provide multi-dimensional assurance that the modernized system behaves identically to the legacy one, both functionally and logically.
