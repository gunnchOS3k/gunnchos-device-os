# Driver classification

{
  "required_open": [
    "virtio",
    "drm-generic",
    "input-evdev",
    "usbhid"
  ],
  "optional_open": [
    "iwlwifi-open-fw",
    "r8169"
  ],
  "deferred_vendor": [
    "gpu-vendor-blob",
    "modem-vendor-fw"
  ],
  "policy": "DEV image includes only open/required classes; vendor blobs deferred"
}
