.PHONY: test validate-configs generate-device-states generate-sbom \
	generate-update-report build-launcher generate-campus-modes generate-contracts \
	export-launcher-contract check-launcher-contract validate-full diagrams e2e smoke gate6-dry-run gate1-boot gate1-dock gate1-test gate1-toolchain

PY := PYTHONPATH=src:.

test:
	pytest -q

validate-full:
	bash scripts/run_full_validation.sh

check-launcher-contract:
	python3 scripts/export_launcher_contract.py
	python3 scripts/check_launcher_contract_fresh.py

validate-configs:
	python3 scripts/validate_configs.py
	python3 scripts/seed_modes.py

generate-device-states:
	$(PY) python3 scripts/generate_device_states.py

generate-sbom:
	$(PY) python3 scripts/generate_sbom.py

generate-update-report:
	python3 scripts/generate_update_report.py

export-launcher-contract:
	python3 scripts/export_launcher_contract.py

build-launcher: export-launcher-contract
	cd apps/launcher_mock && npm run build

generate-campus-modes:
	python3 scripts/generate_all_campus_mode_reports.py

generate-contracts:
	python3 scripts/generate_os_contracts.py

diagrams:
	@echo "Diagrams in docs/diagrams/"

e2e:
	@mkdir -p results/e2e results/campus_device_modes
	$(MAKE) test
	$(MAKE) validate-configs generate-device-states generate-sbom generate-update-report
	$(MAKE) generate-campus-modes generate-contracts
	$(PY) python3 scripts/generate_device_os_e2e.py
	cd apps/launcher_mock && npm run build >> ../../results/e2e/e2e_terminal_output.txt 2>&1 || echo "launcher build skipped"
	python3 scripts/run_all_tool_exports.py 2>> results/e2e/e2e_terminal_output.txt || true
	$(MAKE) e2e-tooling 2>> results/e2e/e2e_terminal_output.txt || true
	python3 scripts/e2e_check_required_artifacts.py

smoke: e2e

e2e-tooling:
	@mkdir -p results/tool_exports
	python3 scripts/run_all_tool_exports.py 2>/dev/null || python3 scripts/check_optional_backends.py || true

e2e-sionna e2e-deepmimo e2e-aerial e2e-oran:
	@echo "Optional target $@ — requires external install; not run in default CI"

# Gate 6 harness only — emulated; OS_PHYSICAL_BOOT_PENDING (not physical boot evidence)
gate6-dry-run:
	python3 scripts/gate6_dry_run.py


# Gate 1 workstreams A/C — software path only (physical pending)
gate1-boot:
	PYTHONPATH=.:src python3 -m gunnchos_device_os.boot --manifest config/boot/sample_manifest.json --out results/gate1/boot_evidence.json

gate1-dock:
	PYTHONPATH=.:src python3 -m gunnchos_device_os.dock --out results/gate1/dock_evidence.json

gate1-test:
	PYTHONPATH=.:src pytest -q tests/test_gate1_identity.py tests/test_gate1_boot_probe.py tests/test_gate1_dock_continuity.py

gate1-toolchain:
	PYTHONPATH=.:src python3 -m gunnchos_device_os.boot --toolchain-check
