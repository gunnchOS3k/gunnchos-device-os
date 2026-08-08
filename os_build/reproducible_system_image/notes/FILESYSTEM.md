# Filesystem layout

{
  "/": "rootfs erofs or squashfs (immutable)",
  "/boot": "ESP + kernel/initrd stubs",
  "/var": "mutable overlay",
  "/var/lib/gunnchos": "runtime persistence",
  "/etc/gunnchos": "policy + profiles",
  "/opt/gunnchos": "shell + packages",
  "/recovery": "recovery ramdisk mount",
  "ab_slots": [
    "slot_a",
    "slot_b"
  ]
}
