#!/usr/bin/env python3
import os, signal, socket, time, json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-current-pin-revalidation")
OUT = ROOT / "artifacts/device_lab_current_pin"
log = OUT / "UNSANDBOX_HELPER_LOG.txt"

def L(m):
    line = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} {m}"
    print(line, flush=True)
    with log.open("a") as fh:
        fh.write(line + "\n")

def kill_pids(pids):
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            L(f"SIGTERM {pid}")
        except ProcessLookupError:
            L(f"gone {pid}")
        except Exception as e:
            L(f"term fail {pid} {e}")
    time.sleep(4)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
            L(f"SIGKILL {pid}")
        except ProcessLookupError:
            L(f"dead {pid}")
        except Exception as e:
            L(f"kill fail {pid} {e}")

def mon_quit(path):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(path)
        s.sendall(b"quit\n")
        s.close()
        L(f"quit {path}")
    except Exception as e:
        L(f"mon_quit fail {path} {e}")

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "cleanup_and_campaign"
    if cmd == "cleanup_and_campaign":
        # quit known monitors
        for mon in Path("/tmp").glob("gdli-*/mon.sock"):
            mon_quit(str(mon))
        # kill known pids + any qemu-system-aarch64 + stuck ring
        pids = []
        try:
            out = subprocess.check_output(["/bin/ps", "-ax", "-o", "pid=,command="], text=True)
            for line in out.splitlines():
                if "qemu-system-aarch64" in line or "run_current_pin_ring_only" in line or "run_current_pin_17c_campaign" in line:
                    try:
                        pids.append(int(line.split()[0]))
                    except Exception:
                        pass
        except Exception as e:
            L(f"ps fail {e}")
            pids.extend([62434, 62439, 61544])
        L(f"targets {pids}")
        kill_pids(pids)
        time.sleep(2)
        # verify free overlays
        try:
            out = subprocess.check_output(["/usr/sbin/lsof"] + [str(p) for p in (ROOT/"os_build/device_lab_interactive_guest/pipeline/overlays").glob("*.qcow2")], text=True, stderr=subprocess.DEVNULL)
            L(f"overlay locks still:\n{out}")
        except Exception as e:
            L(f"no overlay locks ({e})")
        # relaunch campaign
        env = os.environ.copy()
        env.update({
            "GUNNCH_GUEST_AGENT_HOST_STUB": "0",
            "GUNNCHDEVICE_LAB_NET_RESTRICT": "0",
            "GUNNCHDEVICE_LAB_INTERACTIVE_NET": "1",
            "GUNNCH_LAB_INTERACTIVE_GUEST": "1",
            "PYTHONPATH": str(ROOT),
        })
        outf = open(OUT / "CAMPAIGN_17C_STDOUT.txt", "a")
        outf.write(f"\n=== helper relaunch {_utc()} ===\n".replace("_utc()", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        outf.flush()
        py = "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
        subprocess.Popen([py, "scripts/run_current_pin_17c_campaign.py"], cwd=str(ROOT), env=env, stdout=outf, stderr=subprocess.STDOUT, start_new_session=True)
        L("campaign relaunched")
    else:
        L(f"unknown cmd {cmd}")

if __name__ == "__main__":
    main()
