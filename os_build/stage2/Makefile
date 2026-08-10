# Stage 2 OS image build
REPO_ROOT := $(abspath ../..)
PYTHON ?= python3
export PYTHONPATH := $(REPO_ROOT):$(REPO_ROOT)/src:$(PYTHONPATH)

.PHONY: image sysroot clean

image:
	$(PYTHON) $(REPO_ROOT)/scripts/stage2_build_image.py

sysroot:
	$(PYTHON) -c "from pathlib import Path; from gunnchos_device_os.stage2.filesystem import ensure_sysroot; \
print(ensure_sysroot(Path('$(REPO_ROOT)')/'artifacts'/'stage2'/'sysroot').to_dict())"

clean:
	rm -rf $(REPO_ROOT)/artifacts/stage2/image $(REPO_ROOT)/artifacts/stage2/sysroot
