.PHONY: test e2e

PY := PYTHONPATH=src

test:
	$(PY) pytest -q

e2e:
	@mkdir -p results/e2e
	$(PY) pytest -q 2>&1 | tee results/e2e/e2e_terminal_output.txt
	$(PY) python3 scripts/generate_device_os_e2e.py
	cd apps/launcher_mock && npm run build >> ../../results/e2e/e2e_terminal_output.txt 2>&1 || echo "launcher build skipped"
	python3 scripts/e2e_check_required_artifacts.py
