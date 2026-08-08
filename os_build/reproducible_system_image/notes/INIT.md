# Init system

{
  "init": "systemd",
  "targets": [
    "multi-user.target",
    "graphical.target"
  ],
  "gunnchos_units": [
    "gunnchos-runtime.service",
    "gunnchos-updater.service",
    "gunnchos-fleet-agent.service",
    "gunnchos-recovery.target"
  ],
  "claim": "Unit stubs only \u2014 not a shipping initramfs"
}
