.PHONY: test validate-configs generate-device-states generate-sbom \
	reproduce uml supervisor-ready \
	generate-update-report build-launcher generate-campus-modes generate-contracts \
	export-launcher-contract check-launcher-contract validate-full diagrams e2e smoke gate6-dry-run gate1-boot gate1-dock gate1-test gate1-toolchain \
	runtime-services system-image full-product-iii \
	cloud-dev-plane cloud-dev-plane-test cloud-dev-plane-sbom \
	bootable-reference full-product-iv full-product-v full-product-vi full-product-vii \
	bootstrap build package evidence factory-station full-product-viii release-firewall \
	full-product-ix cont-ix-evidence \
	golden-journeys-validate golden-journeys-subset golden-journeys-all golden-journeys-merge-gate \
	device-lab-test device-lab-profile-verify device-lab-wp011 device-lab-g04 device-lab-g06 device-lab-g07 device-lab-g08 \
	wp007-red-team wp007-test wave004 \
	safe-halt-guest base-image-status base-image-seal base-image-overlay base-image-safe-resume

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

device-lab-profile-verify:
	PYTHONPATH=.:src python3 scripts/gunnchctl profile verify

device-lab-wp011:
	PYTHONPATH=.:src python3 scripts/gunnchctl profile verify
	PYTHONPATH=.:src pytest -q tests/device_lab/test_wp011_profile_guest_foundation.py

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

# WP-007 independent security / red-team readiness (digital)
wp007-red-team:
	$(PY) python3 scripts/run_wp007_red_team.py

wp007-test:
	$(PY) python3 scripts/run_wp007_red_team.py
	PYTHONPATH=.:src pytest -q tests/wp007 \
		tests/test_unified_identity.py \
		tests/test_ota_state_machine.py \
		tests/test_sandbox_policy.py \
		tests/phase_xiv/test_phase_xiv.py \
		tests/stage2/test_security.py

# GUNNCHDEVICE_BASE_IMAGE_PIPELINE — operator leave-now + seal/COW (see docs/)
safe-halt-guest:
	$(PY) python3 scripts/gunnchdevice_base_image_pipeline.py safe-halt --reason operator_leaving_now
	@echo "SAFE_HALT written. Do NOT kill -9 QEMU. Do NOT delete sealed qcow2. Resume with: make base-image-safe-resume"

base-image-status:
	$(PY) python3 scripts/gunnchdevice_base_image_pipeline.py status

base-image-seal:
	$(PY) python3 scripts/gunnchdevice_base_image_pipeline.py seal

base-image-overlay:
	$(PY) python3 scripts/gunnchdevice_base_image_pipeline.py overlay --persona $${PERSONA:-session}

base-image-safe-resume:
	$(PY) python3 scripts/gunnchdevice_base_image_pipeline.py safe-resume

# Supervisor-ready digital path (not a shipping OS, not physical boot)
uml:
	@test -f docs/uml/current/use_case.md
	@test -f docs/uml/traceability_matrix.md
	@echo "Mermaid UML in docs/uml/current/; optional: ./docs/uml/render_plantuml.sh"

supervisor-ready:
	$(PY) python3 scripts/generate_service_continuity_profiles.py
	$(PY) python3 scripts/checksum_digital_container_vm.py
	$(PY) python3 scripts/inventory_supervisor_ready.py
	$(PY) python3 -m pytest -q \
		tests/test_service_continuity_profiles.py \
		tests/test_supervisor_ready_uml.py \
		tests/test_device_classes.py \
		tests/test_runtime_profiles.py \
		tests/test_launcher.py \
		tests/test_connectivity_orchestrator.py

reproduce: uml supervisor-ready
	@test -f artifacts/supervisor_ready/SERVICE_CONTINUITY_PROFILES.json
	@test -f artifacts/supervisor_ready/DIGITAL_CONTAINER_VM_CHECKSUMS.json
	@test -f artifacts/supervisor_ready/PHYSICAL_PENDING_INVENTORY.json
	@echo "reproduce complete (digital path only; PHYSICAL_PENDING unchanged)"

# Engineering Wave 004 — platform security + reliability + offline operations
wave004:
	PYTHONPATH=.:src pytest -q tests/test_wave004_platform_security.py
	PYTHONPATH=.:src pytest -q --collect-only tests/test_wave004_platform_security.py >/dev/null
	PYTHONPATH=.:src `head -1 $$(which pytest) | sed 's/#!//' | tr -d ' '` scripts/engineering_wave004/run_wave004_evidence.py
	PYTHONPATH=.:src `head -1 $$(which pytest) | sed 's/#!//' | tr -d ' '` scripts/engineering_wave004/pixel_client_probe.py
	@test -f artifacts/engineering_wave004/WAVE004_RESULT.json
	@test -f artifacts/engineering_wave004/INTEGRITY_REPAIR_RESULT.json
	@test -f artifacts/engineering_wave004/REQUIREMENT_EVALUATOR_MATRIX.json
	@test -f artifacts/engineering_wave004/REQUIREMENT_RESULTS.json
	@test -f artifacts/engineering_wave004/E2E_SCENARIOS_RESULT.json
	@test -f artifacts/engineering_wave004/SECURITY_INJECTION_RESULT.json
	@test -f artifacts/engineering_wave004/CLAIM_BOUNDARIES.json
	@test -f artifacts/engineering_wave004/PIXEL_CLIENT_PROBE.json
	@`head -1 $$(which pytest) | sed 's/#!//' | tr -d ' '` -c "import json; r=json.load(open('artifacts/engineering_wave004/WAVE004_RESULT.json')); assert r['summary']['validated']==12, r['summary']; assert r.get('UNCONDITIONAL_TRUE_CLASSIFIERS', 1)==0"
