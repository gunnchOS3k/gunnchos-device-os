# Capsule-1 Physical Pixel Checklist

Constraints: `adb install -r` only. Never factory reset. Never reboot bootloader. Never wipe unrelated data.

## Preflight
- [ ] Pixel unlocked, USB debugging authorized (`adb devices -l` shows `device`)
- [ ] Baseline refreshed: `make android-capsule` then capture props into `PIXEL6A_BASELINE.json`

## Install
- [ ] `make android-capsule-install`
- [ ] Launcher shows **gunnchOS**
- [ ] Cold launch loads production shell (brand visible)

## P0 workflows
- [ ] Home → Vault → create note → reopen
- [ ] App Center lists apps; no silent install
- [ ] Connect share sheet opens
- [ ] Assist toggles contrast / reduce motion / scale
- [ ] Care shows version + SHA + battery/storage
- [ ] Background app → resume restores surface
- [ ] Exit returns to Android home
- [ ] Back/Home semantics feel OS-like; immersive bars swipe-reveal

## P1
- [ ] WAIKE launch path
- [ ] gunnchAI open assistant (Kirby remains off unless experimental flag)
- [ ] Four-game matrix entries return to Capsule

## Optional guest
- [ ] Do **not** claim QEMU/AVF pass without observed boot/desktop

## Owner gate
- [ ] Hands-on usability → then set `GUNNCHOS_CAPSULE_EXPERIENCE_PARITY=true` if P0 pass

`NEXT_GUNNCHOS_ACTION=OWNER_PIXEL6A_HANDS_ON_CAPSULE_USABILITY_PASS`
