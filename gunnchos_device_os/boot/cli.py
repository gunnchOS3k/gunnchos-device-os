"""gunnchos-boot-probe CLI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evidence import write_evidence
from .failure_injection import FailureMode
from .physical import capture_physical_boot_stub
from .probe import run_boot_probe
from .recovery import recovery_document
from .toolchain import assess_toolchain


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gunnchos-boot-probe",
        description="Gate 1 boot evidence probe (software path; physical pending).",
    )
    p.add_argument(
        "--manifest",
        default="config/boot/sample_manifest.json",
        help="Path to boot manifest JSON",
    )
    p.add_argument(
        "--mode",
        choices=["host-native", "vm-container", "physical-candidate"],
        default="host-native",
    )
    p.add_argument(
        "--failure-mode",
        choices=[m.value for m in FailureMode],
        default="none",
    )
    p.add_argument(
        "--out",
        default="results/gate1/boot_evidence.json",
        help="Evidence JSON output path",
    )
    p.add_argument(
        "--state-dir",
        default="results/gate1/boot_state",
    )
    p.add_argument(
        "--physical-capture",
        action="store_true",
        help="Emit physical evidence capture template (does NOT claim physical boot).",
    )
    p.add_argument(
        "--toolchain-check",
        action="store_true",
        help="Report QEMU/container toolchain status and exit.",
    )
    p.add_argument(
        "--recovery",
        action="store_true",
        help="Print recovery playbook JSON and exit.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.recovery:
        print(json.dumps(recovery_document(), indent=2))
        return 0

    if args.toolchain_check:
        report = assess_toolchain()
        print(json.dumps(report, indent=2))
        return 0 if report.get("offline_software_path") else 2

    if args.physical_capture:
        doc = capture_physical_boot_stub(manifest_path=args.manifest, mode=args.mode)
        out = Path(args.out)
        if out.name == "boot_evidence.json":
            out = out.with_name("physical_boot_capture.json")
        write_evidence(out, doc)
        print(json.dumps(doc, indent=2))
        print(
            "\nStatus: GUNNCHOS_PHYSICAL_BOOT_PENDING "
            "(template written; physical boot NOT complete)",
            file=sys.stderr,
        )
        return 0

    result = run_boot_probe(
        args.manifest,
        mode=args.mode,
        failure_mode=args.failure_mode,
        state_dir=args.state_dir,
    )
    write_evidence(args.out, result.evidence)
    print(json.dumps(result.evidence, indent=2))
    if not result.ok:
        print("Recovery hints:", file=sys.stderr)
        for hint in result.recovery_hints:
            print(f"  - {hint}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
