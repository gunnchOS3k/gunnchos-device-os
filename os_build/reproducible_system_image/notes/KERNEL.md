# Kernel choice (DEV digital path)

{
  "family": "linux",
  "track": "LTS",
  "preferred_version_series": "6.6.x",
  "config_notes": [
    "Enable cgroups v2, namespaces, seccomp, overlayfs for sandbox path",
    "DRM/KMS for dual-display DS-XL; keep vendor blobs out of DEV image",
    "Disable unused wireless firmwares in minimal DEV profile",
    "CONFIG_IKCONFIG_PROC=y for config auditability in DEV images"
  ],
  "claim": "Kernel *choice and config notes* only \u2014 kernel binary not built in this track"
}
