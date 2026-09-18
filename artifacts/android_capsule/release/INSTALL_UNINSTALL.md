# Install / Uninstall — gunnchOS Capsule (Pixel 6a pilot)

## Safety

- Install with `adb install -r` **only**
- Never factory reset, never unlock bootloader, never wipe `/data`
- Never `adb reboot bootloader` as part of Capsule install

## Install

```bash
make android-capsule-install
# or:
adb install -r artifacts/android_capsule/release/gunnchOS-Capsule-Pixel6a-pilot.apk
```

## Uninstall (optional)

```bash
adb uninstall com.gunnchos.capsule
# debug builds:
adb uninstall com.gunnchos.capsule.debug
```

## Owner USB debugging approval

If `adb devices -l` shows `unauthorized`:

1. Unlock Pixel, keep screen on
2. USB File Transfer / MTP
3. Approve “Allow USB debugging?”
4. Re-check `adb devices -l` shows `device`
