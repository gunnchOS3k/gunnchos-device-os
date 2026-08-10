.PHONY: test validate-configs generate-device-states generate-sbom \
	generate-update-report build-launcher generate-campus-modes generate-contracts \
	export-launcher-contract check-launcher-contract validate-full diagrams e2e smoke gate6-dry-run gate1-boot gate1-dock gate1-test gate1-toolchain \
	runtime-services system-image full-product-iii \
	cloud-dev-plane cloud-dev-plane-test cloud-dev-plane-sbom \
	bootable-reference full-product-iv full-product-v full-product-vi full-product-vii \
	bootstrap build package evidence factory-station full-product-viii release-firewall \
	full-product-ix cont-ix-evidence \
	golden-journeys-validate golden-journeys-subset golden-journeys-all golden-journeys-merge-gate \
	device-lab-test device-lab-g04 device-lab-g06 device-lab-g07 device-lab-g08

PY := PYTHONPATH=src:.

# Cont VIII reproducible entrypoints (no host-only secrets/paths)
bootstrap:
	python3 -m pip install -U pip
	python3 -m pip install pytest pyyaml
	@if [ -f requirements.txt ]; then python3 -m pip install -r requirements.txt; fi
	@if [ -f requirements-dev.txt ]; then python3 -m pip install -r requirements-dev.txt; fi
	python3 -m pip install -e ./sdk || python3 -m pip install -e "sdk/[dev]" || true

build:
	$(PY) python3 -c "from gunnchos_device_os.cont_viii.productivity_stack import build_productivity_stack; import json; print(json.dumps(build_productivity_stack(), indent=2))"
	$(PY) python3 -c "from gunnchos_device_os.app_packaging import PackageManifestBuilder; print(PackageManifestBuilder().validate())"

test:
	pytest -q

package:
	@mkdir -p results/cont_viii/package
	$(PY) python3 -c "from gunnchos_device_os.cont_viii.factory_station import run_factory_station; run_factory_station()"
	$(PY) python3 -c "from gunnchos_device_os.cont_viii.release_readiness import evaluate_release_readiness; import json; print(json.dumps(evaluate_release_readiness(write=True), indent=2)[:2000])"
	@cp -f REPRODUCIBILITY_MANIFEST.yaml results/cont_viii/package/ 2>/dev/null || true
	@echo "package artifacts under results/cont_viii/"

evidence: package
	$(PY) python3 scripts/validate_release_readiness_firewall.py
	@test -f results/cont_viii/release_readiness_scorecard.json

factory-station:
	$(PY) python3 -c "from gunnchos_device_os.cont_viii.factory_station import run_factory_station; import json; print(json.dumps(run_factory_station(), indent=2)[:4000])"

full-product-viii:
	PYTHONPATH=.:src pytest -q tests/test_continuation_viii_release_readiness.py
	$(MAKE) evidence

# Cont IX final digital release lock (requires host productivity packages for READY tokens)
full-product-ix:
	PYTHONPATH=.:src pytest -q tests/test_continuation_ix_digital_lock.py
	$(MAKE) cont-ix-evidence

cont-ix-evidence:
	$(PY) python3 -c "from gunnchos_device_os.cont_ix.digital_lock import evaluate_digital_lock; import json; r=evaluate_digital_lock(write=True); print(json.dumps({k:r[k] for k in ('ok','token','earned_tokens','blockers')}, indent=2, default=str)[:4000])"
	@test -f artifacts/continuation_ix/DIGITAL_RELEASE_LOCK.json
	@test -f docs/release/CONTINUATION_IX_DIGITAL_LOCK.md

release-firewall:
	$(PY) python3 scripts/validate_release_readiness_firewall.py

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

# FULL PRODUCT CONTINUATION III — digital runtime + reproducible image path
runtime-services:
	PYTHONPATH=.:src pytest -q tests/test_runtime_services.py

system-image:
	PYTHONPATH=.:src python3 scripts/build_reproducible_system_image.py
	PYTHONPATH=.:src pytest -q tests/test_system_image.py

full-product-iii:
	PYTHONPATH=.:src pytest -q \
		tests/test_runtime_services.py \
		tests/test_system_image.py \
		tests/test_dual_screen_workflows.py \
		tests/test_dock_continuity_sim_suite.py
	PYTHONPATH=.:src python3 scripts/build_reproducible_system_image.py
	PYTHONPATH=.:src python3 scripts/export_runtime_service_matrix.py

# FULL PRODUCT CONTINUATION IV — runnable cloud/fleet/security DEV plane
cloud-dev-plane:
	PYTHONPATH=.:src GUNNCHOS_SERVICE=gateway GUNNCHOS_PORT=8100 python3 -m gunnchos_device_os.cloud_dev_plane

cloud-dev-plane-sbom:
	PYTHONPATH=.:src python3 scripts/generate_cloud_dev_plane_sbom.py

cloud-dev-plane-test:
	PYTHONPATH=.:src pytest -q \
		tests/test_cloud_dev_plane_modes.py \
		tests/test_cloud_dev_plane_outage_resync.py \
		tests/test_cloud_dev_plane_otel.py \
		tests/test_cloud_dev_plane_security_ops.py \
		tests/test_cloud_dev_plane_persistence.py \
		tests/test_adversarial_fuzz_starters.py \
		tests/test_cloud_edge_services.py
	PYTHONPATH=.:src python3 security/dev_ops/sast_hook.py
	PYTHONPATH=.:src python3 scripts/generate_cloud_dev_plane_sbom.py

# Bootable QEMU reference image (DEV/VM evidence; no physical boot claim)
bootable-reference:
	PYTHONPATH=.:src python3 scripts/build_bootable_reference_image.py
	PYTHONPATH=.:src pytest -q tests/test_bootable_reference_image.py

full-product-iv: cloud-dev-plane-test
	PYTHONPATH=.:src pytest -q \
		tests/test_bootable_reference_image.py \
		tests/test_app_packaging.py \
		tests/test_update_recovery_completeness.py \
		tests/test_dual_screen_runtime.py \
		tests/test_dock_continuity_sim_suite.py \
		tests/test_runtime_services.py
	PYTHONPATH=.:src python3 scripts/build_bootable_reference_image.py --build-only

# FULL PRODUCT CONTINUATION V — stub elimination + real IPC + SQLite persistence
full-product-v:
	PYTHONPATH=.:src pytest -q \
		tests/test_runtime_ipc.py \
		tests/test_cloud_dev_plane_persistence.py \
		tests/test_cloud_dev_plane_modes.py \
		tests/test_cloud_dev_plane_outage_resync.py \
		tests/test_bootable_reference_image.py \
		tests/test_runtime_services.py
	PYTHONPATH=.:src python3 scripts/build_bootable_reference_image.py

# FULL PRODUCT CONTINUATION VI — service-specific contracts + app runtime
full-product-vi:
	PYTHONPATH=.:src pytest -q \
		tests/test_continuation_vi_ipc_semantics.py \
		tests/test_continuation_vi_connectivity.py \
		tests/test_continuation_vi_app_runtime.py \
		tests/test_continuation_vi_fleet_lifecycle.py \
		tests/test_continuation_vi_security.py \
		tests/test_runtime_ipc.py \
		tests/test_cloud_dev_plane_persistence.py \
		tests/test_bootable_reference_image.py
	PYTHONPATH=.:src python3 scripts/build_bootable_reference_image.py

# FULL PRODUCT CONTINUATION VII — real packages + platform digital token
full-product-vii:
	PYTHONPATH=.:src pytest -q \
		tests/test_continuation_vii_real_packages.py \
		tests/test_continuation_vi_app_runtime.py \
		tests/test_continuation_vi_ipc_semantics.py \
		tests/test_continuation_vi_connectivity.py \
		tests/test_runtime_ipc.py \
		tests/test_bootable_reference_image.py
	PYTHONPATH=.:src python3 -c "from gunnchos_device_os.app_runtime import AppRuntime; AppRuntime().export_overlay_runtime()"


# Phase XI real-user journey campaign (digital; PHYSICAL_EXECUTION_FREEZE intact)
phase-xi-journeys:
	PYTHONPATH=.:src python3 -m gunnchos_device_os.phase_xi.campaign

phase-xi-representative:
	PYTHONPATH=.:src python3 -m gunnchos_device_os.phase_xi.campaign --representative

phase-xi-test:
	PYTHONPATH=.:src pytest -q tests/test_phase_xi_user_journeys.py

# WP-003 Golden Journey infrastructure (supporting harness — NOT independent verification)
golden-journeys-validate:
	$(PY) python3 scripts/validate_golden_journey_scorecards.py
	PYTHONPATH=.:src pytest -q tests/test_golden_journey_infrastructure.py

golden-journeys-subset:
	$(PY) python3 scripts/run_golden_journey_subset.py --paths-file $${PATHS_FILE:-/dev/null}

golden-journeys-all:
	$(PY) python3 scripts/run_golden_journey_subset.py --all

golden-journeys-merge-gate:
	$(PY) python3 scripts/recommend_merge_golden.py --all

# WP-003R gunnchDevice Lab Foundation v0.1
device-lab-test:
	PYTHONPATH=.:src pytest -q tests/device_lab/test_device_lab_foundation.py

device-lab-g04:
	$(PY) python3 scripts/gunnchctl test GOLDEN-04 --device handheld_docked

device-lab-g06:
	$(PY) python3 scripts/gunnchctl test GOLDEN-06 --device dsxl_coder

device-lab-g07:
	$(PY) python3 scripts/gunnchctl test GOLDEN-07 --device edge_io_rings --rings

device-lab-g08:
	$(PY) python3 scripts/gunnchctl test GOLDEN-08 --device student_14_5 --offline

gunnchctl-devices:
	$(PY) python3 scripts/gunnchctl devices
