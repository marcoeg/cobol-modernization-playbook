SHELL := /bin/bash
PY := python3
.PHONY: parse alloy gen-kotlin gm-legacy gm-diff clean
parse:
	$(PY) scripts/parse_stub.py
alloy: parse
	$(PY) scripts/ir_to_alloy.py
	@echo "Open formal/alloy/banking.als and facts.als in Alloy."
gen-kotlin: parse
	$(PY) scripts/ir_to_kotlin.py
	@echo "Kotlin stubs generated in rewrite/kotlin/"
gm-legacy:
	./scripts/run_golden_master.sh
gm-diff:
	$(PY) scripts/compare_runs.py
clean:
	rm -rf parsing/out formal/alloy/facts.als tests/artifacts out rewrite/kotlin/Generated.kt
