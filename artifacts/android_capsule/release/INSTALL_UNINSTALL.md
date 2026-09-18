# Install / uninstall — gunnchOS Capsule (Pixel 6a pilot)

## Install (safe)
```bash
make android-capsule          # build shell + APK
make android-capsule-install  # adb install -r only
```
Or:
```bash
adb install -r artifacts/android_capsule/release/gunnchOS-Capsule-Pixel6a-pilot.apk
```

**Never** use factory reset, `fastboot`, bootloader reboot, or wipe commands for Capsule-1.

## Uninstall (app only)
```bash
adb uninstall com.gunnchos.capsule.debug
# release id if signed differently:
adb uninstall com.gunnchos.capsule
```
Uninstall removes only this app’s private data — not device-wide wipe.

## SHA-256
See `gunnchOS-Capsule-Pixel6a-pilot.apk.sha256` beside the APK.
