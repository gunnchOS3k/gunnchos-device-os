"""Build deterministic local-only Flatpak repo for org.gunnchos.CX2HTestApp."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from gunnchos_device_os.cx2h.paths import cx2h_lab_root, ensure_lab_tree
from gunnchos_device_os.cx2h.qemu import DEFAULT_SSH_PORT, ensure_ssh_keypair, scp_to_guest, ssh_exec

APP_ID = "org.gunnchos.CX2HTestApp"
RUNTIME_ID = "org.gunnchos.Platform"
REMOTE = "cx2h-local"


def _key_port(repo: Path) -> Tuple[Path, int]:
    lab = cx2h_lab_root(repo)
    key = Path(ensure_ssh_keypair(lab)["private"])
    return key, DEFAULT_SSH_PORT


def _ssh(repo: Path, cmd: str, *, timeout: int = 300):
    key, port = _key_port(repo)
    return ssh_exec(key, port, cmd, timeout=timeout)


def _upload_seeds(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    key, port = _key_port(repo)
    _ssh(repo, "sudo mkdir -p /var/lib/cx2h/flatpak-src /var/lib/cx2h/bin && sudo chown -R gunnchos:gunnchos /var/lib/cx2h", timeout=60)
    results = {}
    for ver in ("v1", "v2"):
        src = lab / "flatpak" / f"app-{ver}"
        # Wipe destination so scp -r does not nest app-vN/app-vN/
        _ssh(repo, f"rm -rf /var/lib/cx2h/flatpak-src/app-{ver} && mkdir -p /var/lib/cx2h/flatpak-src/app-{ver}", timeout=30)
        r = scp_to_guest(key, port, src, f"/var/lib/cx2h/flatpak-src/app-{ver}")
        # If scp placed contents under app-vN/app-vN, flatten
        _ssh(
            repo,
            f"if [ -d /var/lib/cx2h/flatpak-src/app-{ver}/app-{ver} ]; then "
            f"  cp -a /var/lib/cx2h/flatpak-src/app-{ver}/app-{ver}/. /var/lib/cx2h/flatpak-src/app-{ver}/; "
            f"  rm -rf /var/lib/cx2h/flatpak-src/app-{ver}/app-{ver}; "
            f"fi; "
            f"test -f /var/lib/cx2h/flatpak-src/app-{ver}/share/app.py && echo SEED_APP_PY_OK_{ver} || echo SEED_APP_PY_MISSING_{ver}; "
            f"ls -la /var/lib/cx2h/flatpak-src/app-{ver}/share/",
            timeout=30,
        )
        results[ver] = {"rc": r.returncode, "err": (r.stderr or "")[-300:]}
    return results


def build_flatpak_repo(repo: Path) -> Dict[str, Any]:
    ensure_lab_tree(repo)
    upload = _upload_seeds(repo)
    lab = cx2h_lab_root(repo)
    key, port = _key_port(repo)
    script = lab / "scripts" / "build_flatpak_repo.sh"
    scp_to_guest(key, port, script, "/var/lib/cx2h/bin/build_flatpak_repo.sh")
    built = _ssh(
        repo,
        "chmod +x /var/lib/cx2h/bin/build_flatpak_repo.sh; "
        "command -v flatpak; flatpak --version; "
        "command -v ostree || sudo apt-get install -y ostree flatpak 2>/dev/null | tail -5; "
        "bash /var/lib/cx2h/bin/build_flatpak_repo.sh; "
        "echo BUILD_RC=$?",
        timeout=600,
    )
    out = (built.stdout or "") + "\n" + (built.stderr or "")
    ok = (
        "FLATPAK_REPO_BUILT" in out
        and "FLATPAK_REPO_MISSING_APP_REFS" not in out
        and ("VERIFY_INSTALL_OK_1.0.0" in out or "APP_INSTALL_OK_1.0.0" in out)
    )

    refs = _ssh(
        repo,
        "export FLATPAK_USER_DIR=/var/lib/cx2h/flatpak-user; "
        "ostree --repo=/var/lib/cx2h/flatpak-repo refs 2>/dev/null; "
        "ostree --repo=/var/lib/cx2h/flatpak-repo summary -v 2>/dev/null | head -40; "
        "flatpak --user remote-ls cx2h-local 2>/dev/null; "
        "ls -la /var/lib/cx2h/flatpak-repo | head -20",
        timeout=120,
    )
    refs_out = (refs.stdout or "")[-4000:]

    return {
        "schema": "gunnchos.cx2h.flatpak_repo_provenance.v1",
        "app_id": APP_ID,
        "runtime_id": RUNTIME_ID,
        "remote": REMOTE,
        "repo_path_guest": "/var/lib/cx2h/flatpak-repo",
        "user_dir": "/var/lib/cx2h/flatpak-user",
        "versions": {"v1": "1.0.0", "v2": "2.0.0"},
        "external_store_dependency": False,
        "upload": upload,
        "build_ok": ok,
        "build_tail": out[-6000:],
        "refs_tail": refs_out,
        "blocker": None if ok else "CX2H_FLATPAK_REPO_BUILD_FAILED",
    }


def flatpak_provider_state(repo: Path) -> Dict[str, Any]:
    r = _ssh(
        repo,
        "export FLATPAK_USER_DIR=/var/lib/cx2h/flatpak-user; "
        "flatpak --user list --app --columns=application,branch,version,origin 2>/dev/null; "
        "echo '---'; "
        "flatpak --user info org.gunnchos.CX2HTestApp//2.0.0 2>/dev/null || "
        "flatpak --user info org.gunnchos.CX2HTestApp//1.0.0 2>/dev/null || "
        "flatpak --user info org.gunnchos.CX2HTestApp 2>/dev/null || echo NOT_INSTALLED; "
        "echo STATE_DONE",
        timeout=60,
    )
    out = r.stdout or ""
    branches = []
    for line in out.splitlines():
        if APP_ID in line and "\t" in line and "Ref:" not in line and "ID:" not in line:
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].strip() == APP_ID:
                branches.append((parts[1].strip(), (parts[2].strip() if len(parts) > 2 else "")))
    installed = bool(branches) or ("NOT_INSTALLED" not in out and APP_ID in out and "Branch:" in out)
    version = None
    for want in ("2.0.0", "1.0.0", "stable"):
        for b, ver in branches:
            if b == want:
                version = want if want in ("1.0.0", "2.0.0") else (ver or b)
                break
        if version:
            break
    if not version:
        for line in out.splitlines():
            if line.startswith("Branch:"):
                version = line.split(":", 1)[1].strip()
                break
    return {"installed": installed, "version": version, "branches": [b for b, _ in branches], "raw": out[-2000:]}
